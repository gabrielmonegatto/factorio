#!/usr/bin/env python3
"""
snapshot-to-am.py — Save a factory state snapshot to AgentMemory on the VPS.

Usage:
    # Copy to VPS, edit content, execute:
    scp -i ~/.ssh/id_ed25519_factorio snapshot-to-am.py root@187.127.44.153:/tmp/
    ssh -i ~/.ssh/id_ed25519_factorio root@187.127.44.153 'python3 /tmp/snapshot-to-am.py && rm /tmp/snapshot-to-am.py'

Requires: requests, SSH key ~/.ssh/id_ed25519_factorio
Target: AgentMemory on VPS 187.127.44.153:3120
"""
import requests
import subprocess
import sys

VPS_HOST = "187.127.44.153"
AM_PORT = 3120

def get_secret() -> str:
    """Extract AgentMemory secret from the container's /proc/1/environ."""
    result = subprocess.run(
        ["docker", "exec", "factorio_agent_memory", "sh", "-c",
         "cat /proc/1/environ | tr '\\000' '\\n' | grep AGENTMEMORY_SECRET | cut -d= -f2"],
        capture_output=True, text=True
    )
    return result.stdout.strip()


def save_snapshot(content: str, tags: list = None) -> dict:
    """POST a memory to AgentMemory. Returns response JSON dict."""
    if tags is None:
        tags = ["fabrica:snapshot"]
    secret = get_secret()
    resp = requests.post(
        f"http://localhost:{AM_PORT}/agentmemory/remember",
        headers={"Authorization": f"Bearer {secret}", "Content-Type": "application/json"},
        json={"content": content, "type": "state", "tags": tags}
    )
    return {"status": resp.status_code, "body": resp.text[:500]}


def list_memories() -> list:
    """List all memories from AgentMemory."""
    secret = get_secret()
    resp = requests.get(
        f"http://localhost:{AM_PORT}/agentmemory/memories",
        headers={"Authorization": f"Bearer {secret}"}
    )
    if resp.status_code == 200:
        return resp.json().get("memories", [])
    return []


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        mems = list_memories()
        print(f"Total memories: {len(mems)}")
        for m in mems:
            title = m.get("content", "?")[:100]
            mtype = m.get("type", "?")
            print(f"  [{mtype}] {title}")
        sys.exit(0)

    # Default snapshot — edit content before running
    content = "SNAPSHOT from factory pulse. See AgentMemory for details."
    result = save_snapshot(content)
    print(f"Status: {result['status']}")
    print(f"Response: {result['body']}")