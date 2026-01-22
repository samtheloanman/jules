
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

def check_sessions():
    key = get_api_key()
    if not key:
        print("No API key found")
        return

    url = "https://jules.googleapis.com/v1alpha/sessions"
    req = urllib.request.Request(url, headers={"X-Goog-Api-Key": key})
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        sessions = data.get("sessions", [])
        print(f"Total sessions found: {len(sessions)}")
        
        for s in sessions:
            name = s.get("name")
            id = name.split("/")[-1]
            state = s.get("state")
            
            # Get detail
            detail_url = f"https://jules.googleapis.com/v1alpha/{name}"
            detail_req = urllib.request.Request(detail_url, headers={"X-Goog-Api-Key": key})
            try:
                detail_resp = urllib.request.urlopen(detail_req)
                detail_data = json.loads(detail_resp.read().decode())
                
                keys = list(detail_data.keys())
                if "turns" in detail_data:
                    print(f"Session {id} ({state}) HAS TURNS: {len(detail_data['turns'])}")
                else:
                    # print(f"Session {id} ({state}) no turns. Keys: {keys}")
                    pass
            except Exception as e:
                print(f"Error checking session {id}: {e}")
                
    except Exception as e:
        print(f"Error listing sessions: {e}")

if __name__ == "__main__":
    check_sessions()
