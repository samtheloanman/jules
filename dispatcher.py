"""
Task Dispatcher Module
Dispatches tasks to AI agents (Jules, Claude, Gemini, Antigravity)
"""

import subprocess
import json
import os
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
import uuid


class TaskDispatcher:
    """Dispatch tasks to various AI agents and track their status."""
    
    REPO_NAME = "samtheloanman/unified-cmtg"
    
    def __init__(self):
        # State directory for tracking dispatched tasks
        # Dynamic root detection: dispatcher.py is in jules/ -> root is same dir
        self.root_dir = Path(__file__).resolve().parent
        self.state_dir = self.root_dir / ".conductor-state"
        self.state_dir.mkdir(exist_ok=True)
        
        self.tasks_file = self.state_dir / "dispatched_tasks.json"
        self.heartbeats_file = self.state_dir / "agent_heartbeats.json"
        
        # Initialize files if they don't exist
        if not self.tasks_file.exists():
            self._save_tasks({"tasks": [], "last_updated": None})
        if not self.heartbeats_file.exists():
            self._save_heartbeats({})
    
    def _load_tasks(self) -> Dict:
        """Load dispatched tasks from JSON file."""
        try:
            return json.loads(self.tasks_file.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return {"tasks": [], "last_updated": None}
    
    def _save_tasks(self, data: Dict):
        """Save dispatched tasks to JSON file."""
        data["last_updated"] = datetime.now().isoformat()
        self.tasks_file.write_text(json.dumps(data, indent=2))
    
    def _load_heartbeats(self) -> Dict:
        """Load agent heartbeats."""
        try:
            return json.loads(self.heartbeats_file.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_heartbeats(self, data: Dict):
        """Save agent heartbeats."""
        self.heartbeats_file.write_text(json.dumps(data, indent=2))
    
    def _update_heartbeat(self, agent: str, status: str):
        """Update the heartbeat for an agent."""
        heartbeats = self._load_heartbeats()
        heartbeats[agent] = {
            "status": status,
            "last_seen": datetime.now().isoformat()
        }
        self._save_heartbeats(heartbeats)
    
    def _add_task_record(self, task_id: str, agent: str, task_description: str, 
                         status: str, result: Optional[str] = None):
        """Add a task record to the tracking file."""
        data = self._load_tasks()
        data["tasks"].append({
            "id": task_id,
            "agent": agent,
            "task": task_description,
            "status": status,
            "result": result,
            "dispatched_at": datetime.now().isoformat(),
            "completed_at": None
        })
        self._save_tasks(data)
    
    def dispatch_to_jules(self, task_description: str, branch: str = "main", repo_name: str = None) -> Dict:
        """
        Dispatch a task to Jules via the Jules REST API.
        
        The API creates a new session with the task as a prompt.
        See: https://jules.googleapis.com/v1alpha/sessions
        
        Args:
            task_description: The task to send to Jules
            branch: Git branch to work on (default: main)
            repo_name: Specific repository to target. If None, defaults to self.REPO_NAME
            
        Returns:
            Dict with status, task_id, session_id, and any output/error
        """
        target_repo = repo_name or self.REPO_NAME
        task_id = str(uuid.uuid4())[:8]
        
        # Get Jules API key
        jules_api_key = os.environ.get("JULES_API_KEY")
        
        if not jules_api_key:
            # Check MCP secrets file first
            secrets_file = Path("/Volumes/samalabam/code/custom-cmre-mcp/config/secrets.json")
            if secrets_file.exists():
                try:
                    secrets = json.loads(secrets_file.read_text())
                    jules_api_key = secrets.get("jules", {}).get("api_key")
                except:
                    pass

        if not jules_api_key:
            # Check env files
            for env_name in [".env.local", ".env"]:
                env_file = self.root_dir / env_name
                if env_file.exists():
                    for line in env_file.read_text().splitlines():
                        if line.startswith("JULES_API_KEY=") or line.startswith("GEMINI_API_KEY_AI_STUDIO="):
                            jules_api_key = line.split("=", 1)[1].strip().strip("'\"")
                            break
                if jules_api_key: break
        
        if not jules_api_key:
            return self._queue_jules_task(task_id, task_description, "Missing JULES_API_KEY")
        
        self._update_heartbeat("Jules", "dispatching")
        
        # 1. List sources
        try:
            req = urllib.request.Request(
                "https://jules.googleapis.com/v1alpha/sources",
                headers={
                    "X-Goog-Api-Key": jules_api_key,
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status != 200:
                    return self._queue_jules_task(task_id, task_description, f"List sources failed: {response.status}")
                sources = json.loads(response.read().decode()).get("sources", [])
        except Exception as e:
            return self._queue_jules_task(task_id, task_description, f"List sources error: {e}")

        # debug mode
        if target_repo == "LIST_SOURCES":
            found = []
            for s in sources:
                r = s.get("githubRepo", {})
                if r: found.append(f"{r.get('owner')}/{r.get('repo')}")
            if sources:
                print(f"DEBUG Source 0: {sources[0]}")
            return {"success": True, "message": f"Repos: {', '.join(found)}"}

        # 2. Match Repo
        source_name = None
        for source in sources:
            s_id = source.get("id", "")
            s_name = source.get("name", "")
            r_info = source.get("githubRepo", {})
            r_name = r_info.get("repo", "")
            owner = r_info.get("owner", "")
            full = f"{owner}/{r_name}"
            
            if target_repo.lower() in full.lower() or target_repo.lower() in s_id.lower():
                source_name = s_name
                break
            if target_repo.split("/")[-1].lower() == r_name.lower():
                source_name = s_name
                break
        
        if not source_name:
            # Fallback: Construct the source name manually to force dispatch
            # Format: sources/github/{owner}/{repo}
            if "/" in target_repo:
                print(f"Warning: {target_repo} not found in sources. Forcing dispatch with constructed ID.")
                source_name = f"sources/github/{target_repo}"
            else:
                 return self._queue_jules_task(task_id, task_description, f"Repo {target_repo} not found in sources.")

        # 3. Create Session
        full_prompt = f"[Repository: {target_repo}]\n\n{task_description}"
        try:
            s_req = urllib.request.Request(
                "https://jules.googleapis.com/v1alpha/sessions",
                headers={
                    "X-Goog-Api-Key": jules_api_key,
                    "Content-Type": "application/json"
                },
                data=json.dumps({"prompt": full_prompt}).encode('utf-8'),
                method="POST"
            )
            with urllib.request.urlopen(s_req, timeout=60) as resp:
                if resp.status in [200, 201]:
                    s_data = json.loads(resp.read().decode())
                    s_id = s_data.get("name", "").split("/")[-1]
                    self._add_task_record(task_id, "Jules", task_description, "dispatched", f"Session: {s_id}")
                    self._update_heartbeat("Jules", "active")
                    return {
                        "success": True, 
                        "task_id": task_id, 
                        "session_id": s_id, 
                        "message": f"✅ Dispatched to {target_repo}! Session: {s_id}",
                        "session_url": f"https://jules.google.com/session/{s_id}"
                    }
                else:
                    return self._queue_jules_task(task_id, task_description, f"API error {resp.status}")
        except Exception as e:
            return self._queue_jules_task(task_id, task_description, f"Session create error: {e}")
    
    def _queue_jules_task(self, task_id: str, task_description: str, reason: str = None) -> Dict:
        """Queue a Jules task for manual execution when API is unavailable."""
        self._add_task_record(task_id, "Jules", task_description, "queued")
        self._update_heartbeat("Jules", "has_pending")
        
        # Write to Jules queue file
        queue_file = self.state_dir / "jules_queue.json"
        try:
            queue = json.loads(queue_file.read_text()) if queue_file.exists() else {"tasks": []}
        except:
            queue = {"tasks": []}
        
        queue["tasks"].append({
            "id": task_id,
            "task": task_description,
            "repo": self.REPO_NAME,
            "status": "pending",
            "reason": reason,
            "created_at": datetime.now().isoformat()
        })
        queue_file.write_text(json.dumps(queue, indent=2))
        
        msg = "Task queued for Jules"
        if reason:
            msg += f" ({reason})"
        msg += ". Set JULES_API_KEY to enable automatic dispatch."
        
        return {
            "success": False,
            "task_id": task_id,
            "message": msg,
            "queued": True
        }
    
    def dispatch_to_claude(self, task_description: str, workspace: str = None) -> Dict:
        """
        Dispatch a task to Claude via the Anthropic Messages API.
        
        Creates a conversation that is logged to a file for monitoring.
        Uses streaming to capture real-time output.
        
        Args:
            task_description: The task to send to Claude
            workspace: Optional workspace path (for context in prompt)
            
        Returns:
            Dict with status, session_id, and output log path
        """
        task_id = str(uuid.uuid4())[:8]
        workspace = workspace or "/home/samalabam/code/unified-cmtg"
        
        # Get Claude API key
        claude_api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if not claude_api_key:
            # Check MCP secrets file
            secrets_file = Path("/Volumes/samalabam/code/custom-cmre-mcp/config/secrets.json")
            if secrets_file.exists():
                try:
                    secrets = json.loads(secrets_file.read_text())
                    claude_api_key = secrets.get("global", {}).get("ANTHROPIC_API_KEY")
                except:
                    pass
        
        if not claude_api_key:
            # Fall back to CLI
            return self._dispatch_claude_cli(task_id, task_description, workspace)
        
        try:
            self._update_heartbeat("Claude", "dispatching")
            
            # Create context-aware system prompt
            system_prompt = f"""You are Claude, an AI assistant helping with coding tasks.
            
Workspace: {workspace}
Repository: {self.REPO_NAME}

You have access to the codebase and should provide actionable coding assistance.
When given a task, analyze it carefully and provide implementation details."""

            # Make API request (Claude API support removed for urllib compatibility - use CLI fallback)
            # To fix: Implement urllib call here or rely on CLI
            raise Exception("Use CLI for Claude")
            """
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                ...
            )
            """
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("content", [])
                output_text = ""
                for block in content:
                    if block.get("type") == "text":
                        output_text += block.get("text", "")
                
                # Save conversation to log file
                log_file = self.state_dir / f"claude_session_{task_id}.md"
                log_content = f"""# Claude Session {task_id}
**Created**: {datetime.now().isoformat()}
**Workspace**: {workspace}

## Task
{task_description}

## Response
{output_text}
"""
                log_file.write_text(log_content)
                
                self._add_task_record(task_id, "Claude", task_description, "completed", 
                    f"Session logged to: {log_file}")
                self._update_heartbeat("Claude", "active")
                
                return {
                    "success": True,
                    "task_id": task_id,
                    "message": f"✅ Claude responded! View session: claude_session_{task_id}.md",
                    "output": output_text[:500] + "..." if len(output_text) > 500 else output_text,
                    "log_file": str(log_file),
                    "model": result.get("model"),
                    "usage": result.get("usage")
                }
            else:
                error_msg = response.text[:200]
                self._add_task_record(task_id, "Claude", task_description, "failed", error_msg)
                return {
                    "success": False,
                    "task_id": task_id,
                    "message": f"Claude API error {response.status_code}: {error_msg}"
                }
                
        except requests.Timeout:
            return {
                "success": False,
                "task_id": task_id,
                "message": "Claude API request timed out after 180 seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "task_id": task_id,
                "message": f"Error dispatching to Claude: {str(e)}"
            }
    
    def _dispatch_claude_cli(self, task_id: str, task_description: str, workspace: str) -> Dict:
        """Fallback to Claude CLI when API key is not available."""
        try:
            cmd = ["claude", "-p", task_description]
            
            self._update_heartbeat("Claude", "dispatching")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=workspace
            )
            
            if result.returncode == 0:
                self._add_task_record(task_id, "Claude", task_description, "dispatched", result.stdout)
                self._update_heartbeat("Claude", "active")
                return {
                    "success": True,
                    "task_id": task_id,
                    "message": "Task dispatched to Claude Code CLI",
                    "output": result.stdout
                }
            else:
                self._add_task_record(task_id, "Claude", task_description, "failed", result.stderr)
                return {
                    "success": False,
                    "task_id": task_id,
                    "message": "Claude CLI dispatch failed",
                    "error": result.stderr
                }
                
        except FileNotFoundError:
            return {
                "success": False,
                "task_id": task_id,
                "message": "Claude CLI not found and API key not set. Set ANTHROPIC_API_KEY."
            }
        except Exception as e:
            return {
                "success": False,
                "task_id": task_id,
                "message": f"Error dispatching to Claude: {str(e)}"
            }

    
    def dispatch_to_gemini(self, task_description: str, workspace: str = None) -> Dict:
        """
        Dispatch a task to Gemini CLI.
        
        Args:
            task_description: The task to send to Gemini
            workspace: Optional workspace path
            
        Returns:
            Dict with status and any output/error
        """
        task_id = str(uuid.uuid4())[:8]
        workspace = workspace or "/home/samalabam/code/unified-cmtg"
        
        try:
            # Gemini CLI command
            cmd = ["gemini", "-p", task_description]
            
            self._update_heartbeat("Gemini", "dispatching")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=workspace
            )
            
            if result.returncode == 0:
                self._add_task_record(task_id, "Gemini", task_description, "dispatched", result.stdout)
                self._update_heartbeat("Gemini", "active")
                return {
                    "success": True,
                    "task_id": task_id,
                    "message": "Task dispatched to Gemini CLI",
                    "output": result.stdout
                }
            else:
                self._add_task_record(task_id, "Gemini", task_description, "failed", result.stderr)
                return {
                    "success": False,
                    "task_id": task_id,
                    "message": "Gemini dispatch failed",
                    "error": result.stderr
                }
                
        except FileNotFoundError:
            return {
                "success": False,
                "task_id": task_id,
                "message": "Gemini CLI not found. Please install gemini CLI."
            }
        except Exception as e:
            return {
                "success": False,
                "task_id": task_id,
                "message": f"Error dispatching to Gemini: {str(e)}"
            }
    
    def queue_for_antigravity(self, task_description: str) -> Dict:
        """
        Queue a task for Antigravity (adds to companion inbox for approval).
        
        Args:
            task_description: The task to queue
            
        Returns:
            Dict with status
        """
        task_id = str(uuid.uuid4())[:8]
        
        # Write to companion inbox file
        # Write to companion inbox file
        inbox_file = self.state_dir / "antigravity_inbox.json"
        
        try:
            inbox = json.loads(inbox_file.read_text()) if inbox_file.exists() else {"items": []}
        except:
            inbox = {"items": []}
        
        inbox["items"].append({
            "id": task_id,
            "task": task_description,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        })
        
        inbox_file.write_text(json.dumps(inbox, indent=2))
        self._add_task_record(task_id, "Antigravity", task_description, "queued")
        self._update_heartbeat("Antigravity", "has_pending")
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "Task queued for Antigravity. Check companion inbox for approval."
        }
    
    def get_dispatched_tasks(self, agent: str = None, limit: int = 10) -> List[Dict]:
        """Get recent dispatched tasks, optionally filtered by agent."""
        data = self._load_tasks()
        tasks = data.get("tasks", [])
        
        if agent:
            tasks = [t for t in tasks if t.get("agent") == agent]
        
        # Return most recent first
        return sorted(tasks, key=lambda x: x.get("dispatched_at", ""), reverse=True)[:limit]
    
    def get_agent_status(self, agent: str) -> Dict:
        """Get the current status of an agent."""
        heartbeats = self._load_heartbeats()
        return heartbeats.get(agent, {"status": "unknown", "last_seen": None})
    
    def get_all_agent_statuses(self) -> Dict:
        """Get status of all agents."""
        return self._load_heartbeats()


# Convenience functions
def dispatch_task(agent: str, task: str, **kwargs) -> Dict:
    """Dispatch a task to the specified agent."""
    dispatcher = TaskDispatcher()
    
    if agent.lower() == "jules":
        return dispatcher.dispatch_to_jules(task, repo_name=kwargs.get("repo"))
    elif agent.lower() == "claude":
        return dispatcher.dispatch_to_claude(task, kwargs.get("workspace"))
    elif agent.lower() == "gemini":
        return dispatcher.dispatch_to_gemini(task, kwargs.get("workspace"))
    elif agent.lower() == "antigravity":
        return dispatcher.queue_for_antigravity(task)
    else:
        return {"success": False, "message": f"Unknown agent: {agent}"}


if __name__ == "__main__":
    # Test the dispatcher
    dispatcher = TaskDispatcher()
    print("Agent statuses:", dispatcher.get_all_agent_statuses())
    print("Recent tasks:", dispatcher.get_dispatched_tasks(limit=5))
