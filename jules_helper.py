
import os
import json
import urllib.request
import urllib.error
import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

class JulesHelper:
    def __init__(self):
        # jules_helper.py is in jules/ -> root is same dir
        self.root_dir = Path(__file__).resolve().parent
        self.state_dir = self.root_dir / ".conductor-state"
        self.tasks_file = self.state_dir / "dispatched_tasks.json"
        self.api_key = self._get_api_key()
        
    def _get_api_key(self) -> str:
        key = os.environ.get("JULES_API_KEY")
        if not key:
            # Check .env.local first (Next.js standard) then .env
            for env_name in [".env.local", ".env"]:
                env_file = self.root_dir / env_name
                if env_file.exists():
                    # print(f"Reading {env_name} file...")
                    filtered_lines = [l for l in env_file.read_text().splitlines() if "=" in l]
                    for line in filtered_lines:
                        if line.startswith("JULES_API_KEY=") or line.startswith("GEMINI_API_KEY_AI_STUDIO="):
                            # Prefer JULES_API_KEY, but fallback to GEMINI Studio key if mostly compatible
                            val = line.split("=", 1)[1].strip().strip("'\"")
                            if line.startswith("JULES_API_KEY="):
                                key = val
                                break
                            elif not key: # Keep looking but store this as fallback
                                key = val
                    if key: break
        return key

    def get_active_sessions(self) -> List[Dict]:
        """Read dispatched tasks to find Jules sessions."""
        if not self.tasks_file.exists():
            return []
        
        try:
            data = json.loads(self.tasks_file.read_text())
            tasks = data.get("tasks", [])
            # Filter for tasks assigned to Jules that have a result containing "Session:"
            jules_sessions = []
            for t in tasks:
                if t.get("agent") == "Jules" and t.get("result"):
                    # Extract session ID from result string "Session: <id>"
                    if "Session: " in t["result"]:
                        session_id = t["result"].split("Session: ")[1].strip()
                        jules_sessions.append({
                            "task_id": t["id"],
                            "task_desc": t["task"],
                            "session_id": session_id,
                            "timestamp": t.get("dispatched_at")
                        })
            return jules_sessions
        except Exception as e:
            print(f"Error reading tasks file: {e}")
            return []

    def list_remote_sessions(self) -> List[Dict]:
        """Try to list sessions directly from the API."""
        if not self.api_key:
            print("Error: JULES_API_KEY not found.")
            return []

        url = "https://jules.googleapis.com/v1alpha/sessions"
        req = urllib.request.Request(url, headers={"X-Goog-Api-Key": self.api_key})
        
        try:
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    return data.get("sessions", [])
                else:
                    print(f"Failed to list remote sessions: {response.status}")
                    return []
        except urllib.error.HTTPError as e:
            print(f"HTTP Error listing sessions: {e.code} {e.reason}")
            # print(e.read().decode())
            return []
        except Exception as e:
            print(f"Request failed: {e}")
            return []

    def check_session_status(self, session_id: str):
        """Fetch session details from Jules API."""
        if not self.api_key:
            print("Error: JULES_API_KEY not found.")
            return

        # Try various endpoint patterns
        url = f"https://jules.googleapis.com/v1alpha/sessions/{session_id}"
        if "/" in session_id:
             url = f"https://jules.googleapis.com/v1alpha/{session_id}"

        req = urllib.request.Request(url, headers={"X-Goog-Api-Key": self.api_key})

        try:
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    return json.loads(response.read().decode())
                else:
                    return {"error": response.status}
        except urllib.error.HTTPError as e:
            return {"error": e.code, "text": e.read().decode()}
        except Exception as e:
            print(f"Request failed: {e}")
            return None

    def ask_gemini(self, question: str, context: str = "") -> str:
        """Ask Gemini CLI for an answer."""
        prompt = f"""You are a helpful assistant for the 'unified-cmtg' project.
        Another agent (Jules) has a question about a task.
        
        Context Task: {context}
        
        Question: {question}
        
        Please provide a concise, technical answer based on your knowledge of the project structure and common practices.
        """
        
        try:
            cmd = ["gemini", "-p", prompt]
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.root_dir
            )
            if result.returncode == 0:
                self.log(f"Gemini Answered: {result.stdout.strip()[:50]}...")
                return result.stdout.strip()
            else:
                return f"Error querying Gemini: {result.stderr}"
        except FileNotFoundError:
            return "Gemini CLI not found."

    def log(self, msg: str):
        print(f"[JulesHelper] {msg}")

    
    def reply_to_session(self, session_id: str, message: str) -> bool:
        """Send a reply to a Jules session."""
        url = f"https://jules.googleapis.com/v1alpha/sessions/{session_id}:continue"
        
        data = {"prompt": message}
        req = urllib.request.Request(
            url,
            headers={
                "X-Goog-Api-Key": self.api_key,
                "Content-Type": "application/json"
            },
            data=json.dumps(data).encode('utf-8'),
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.status in [200, 201]
        except urllib.error.HTTPError as e:
            print(f"Error replying to session {session_id}: {e}")
            return False
        except Exception as e:
            print(f"Error replying to session {session_id}: {e}")
            return False

    def get_session_details(self, session_id: str) -> Optional[Dict]:
        """Fetch full details of a session including history."""
        url = f"https://jules.googleapis.com/v1alpha/sessions/{session_id}"
        req = urllib.request.Request(
            url,
            headers={"X-Goog-Api-Key": self.api_key}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            print(f"Error fetching session {session_id}: {e}")
            return None

    def is_asking_question(self, content: str) -> bool:
        """Use Gemini to determine if Jules is asking for something."""
        prompt = f"""Analyze the following message from an AI coding agent named Jules. 
Determine if Jules is asking for clarification, information, feedback, or a decision from a human.

Message: "{content}"

If Jules is clearly waiting for a human response or asking a question (even without a question mark), answer only with the word 'YES'.
If Jules is just providing an update, stating a conclusion, or finishing a task without needing input, answer only with the word 'NO'.

Answer:"""
        try:
            cmd = ["gemini", "-p", prompt]
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.root_dir
            )
            if result.returncode == 0:
                response = result.stdout.strip().upper()
                return "YES" in response
            return False
        except:
            return "?" in content # Fallback

    def monitor_and_assist(self):
        """Monitor active sessions and answer questions using Gemini."""
        print("Starting Jules Monitor & Assist Agent (Intelligent Mode)...")
        print("Press Ctrl+C to stop.")
        
        processed_turn_ids = set()

        while True:
            try:
                # Get list of recent sessions (usually top 30-50)
                sessions = self.list_remote_sessions()
                print(f"Checking {len(sessions)} sessions for questions...")
                
                for session in sessions:
                    session_id = session.get("name", "").split("/")[-1]
                    state = session.get("state")
                    print(f"  Checking session {session_id} (State: {state})...")
                    
                    # Only check active sessions or specifically waiting ones
                    if state not in ["STATE_ACTIVE", "PLANNING", "AWAITING_USER_FEEDBACK", "AWAITING_PLAN_APPROVAL"]:
                        continue
                        
                    # Get full details to see the conversation turns
                    details = self.get_session_details(session_id)
                    if not details: continue
                    
                    turns = details.get("turns", [])
                    if not turns: continue
                    
                    last_turn = turns[-1]
                    # We use session_id + turn index as a unique ID for the turn
                    turn_unique_id = f"{session_id}-{len(turns)}"
                    
                    if turn_unique_id in processed_turn_ids:
                        continue
                        
                    role = last_turn.get("role", "")
                    content = last_turn.get("content", "")
                    
                    # If last message is from Jules (MODEL), use Gemini to check if it's a question
                    if role == "ROLE_MODEL":
                        print(f"  Analyzing message in session {session_id}...")
                        if self.is_asking_question(content):
                            print(f"\n[?] Input Requested in session {session_id}:")
                            print(f"    \"{content[:150]}...\"")
                            
                            # Ask Gemini
                            print("    Asking Gemini for an answer...")
                            answer = self.ask_gemini(content, context=f"Session {session_id}")
                            
                            if answer and not "Error" in answer:
                                print(f"    Gemini Suggests: {answer[:50]}...")
                                print("    Sending reply...")
                                if self.reply_to_session(session_id, answer):
                                    print("    ✅ Reply sent successfully.")
                                    processed_turn_ids.add(turn_unique_id)
                                else:
                                    print("    ❌ Failed to reply.")
                            else:
                                print("    ❌ Gemini could not answer.")
                        else:
                            # Not a question, mark as processed so we don't analyze again
                            processed_turn_ids.add(turn_unique_id)
                                
                    processed_turn_ids.add(turn_unique_id)

                time.sleep(30)
                
            except KeyboardInterrupt:
                print("\nStopping monitor...")
                break
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(30)

if __name__ == "__main__":
    helper = JulesHelper()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "list":
            sessions = helper.get_active_sessions()
            for s in sessions:
                print(f"{s['session_id']} - {s['task_desc'][:50]}...")
        elif cmd == "remote-list":
            sessions = helper.list_remote_sessions()
            print(json.dumps(sessions, indent=2))
        elif cmd == "check" and len(sys.argv) > 2:
            data = helper.check_session_status(sys.argv[2])
            print(json.dumps(data, indent=2))
        elif cmd == "monitor":
            helper.monitor_and_assist()
        else:
            print("Usage: python jules_helper.py [list|check <id>|monitor]")
    else:
        helper.monitor_and_assist()
