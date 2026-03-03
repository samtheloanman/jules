
import urllib.request
import json
import os
from pathlib import Path

def get_api_key():
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("JULES_API_KEY="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return os.environ.get("JULES_API_KEY")

def test_endpoints():
    key = get_api_key()
    base = "https://jules.googleapis.com/v1alpha"
    
    # Get all session ids
    sessions_url = f"{base}/sessions"
    req_list = urllib.request.Request(sessions_url, headers={"X-Goog-Api-Key": key})
    session_ids = [s['name'].split('/')[-1] for s in json.loads(urllib.request.urlopen(req_list).read().decode()).get('sessions', [])]
    
    potential_suffixes = [
        "",
        ":getPlan",
        ":listTurns",
        ":history",
        ":listMessages",
        ":chat",
        "/turns",
        "/messages",
        "/plan",
    ]
    
    for session_id in session_ids:
        print(f"Checking session {session_id}...")
        for suffix in potential_suffixes:
            url = f"{base}/sessions/{session_id}{suffix}"
            req = urllib.request.Request(url, headers={"X-Goog-Api-Key": key})
            try:
                resp = urllib.request.urlopen(req, timeout=3)
                data = json.loads(resp.read().decode())
                # print(f"  Success: {suffix}")
                if "turns" in data or "messages" in data or "history" in data or "chat" in data:
                    print(f"  !!! DATA FOUND at {url}")
                    print(f"  Keys: {list(data.keys())}")
                    return
            except:
                pass

if __name__ == "__main__":
    test_endpoints()
