
import subprocess
import json
import os

def check_pull_requests():
    repo = "samtheloanman/unified-cmtg"
    try:
        # Get last 10 PRs
        cmd = ["gh", "pr", "list", "--repo", repo, "--state", "all", "--limit", "10", "--json", "number"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error listing PRs: {result.stderr}")
            return
        
        pr_list = json.loads(result.stdout)
        
        for pr in pr_list:
            pr_num = pr['number']
            # Get comments
            cmd = ["gh", "pr", "view", str(pr_num), "--repo", repo, "--json", "comments,reviews"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                continue
            
            data = json.loads(result.stdout)
            comments = data.get("comments", [])
            reviews = data.get("reviews", [])
            
            all_text = []
            for c in comments:
                if "jules" in c.get("author", {}).get("login", "").lower():
                    all_text.append(c.get("body", ""))
            
            for r in reviews:
                if "jules" in r.get("author", {}).get("login", "").lower():
                    all_text.append(r.get("body", ""))
                    # Check review comments
                    for rc in r.get("comments", []):
                        all_text.append(rc.get("body", ""))

            if all_text:
                print(f"--- PR #{pr_num} Jules Activity ---")
                for text in all_text:
                    # Clean up Jules intro/footer if needed, or just print first 500 chars
                    print(text[:500] + "...")
                    print("-" * 20)
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_pull_requests()
