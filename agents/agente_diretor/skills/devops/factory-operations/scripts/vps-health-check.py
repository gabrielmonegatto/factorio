#!/usr/bin/env python3
"""
VPS Health Check — Fabrica EternalL
======================================
Reusable script that SSHs into the VPS with password auth and runs the full
diagnostic checklist. Designed for environments without sshpass (Windows/git-bash).

Usage:
    # From Hermes agent (recommended via subagent delegation):
    # 1. Write this script on the VPS or in a temp dir
    # 2. Run: python vps-health-check.py

    # Or pipe commands sequentially:
    ssh root@187.127.44.153 "$(cat <<'CMDS'
    docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
    docker exec factorio_agents cat /root/.hermes/gateway_state.json
    docker exec factorio_agents ps aux | grep hermes | grep -v grep
    docker exec factorio_agents tail -20 /var/log/hermes_gateway.log
    df -h /
    free -h
    uptime
CMDS
)"

Requires: sshpass (if used locally) or delegation to a subagent.
"""
import json
import subprocess
import sys

# --- Config ---
VPS_HOST = "187.127.44.153"
VPS_USER = "root"
VPS_PASS = ".gmIN&QAY8Q'L9vS"  # nosec — VPS credential
CONTAINER = "factorio_agents"

COMMANDS = [
    ("Containers", f"docker ps --format 'table {{{{.Names}}}}\t{{{{.Status}}}}\t{{{{.Ports}}}}'"),
    ("Gateway State", f"docker exec {CONTAINER} cat /root/.hermes/gateway_state.json 2>/dev/null || echo 'NOT_FOUND'"),
    ("Gateway Process", f"docker exec {CONTAINER} ps aux | grep hermes | grep -v grep || echo 'NO_HERMES_PROCESS'"),
    ("Gateway Log (last 20)", f"docker exec {CONTAINER} tail -20 /var/log/hermes_gateway.log 2>/dev/null || echo 'LOG_NOT_FOUND'"),
    ("Disk", "df -h / | tail -1"),
    ("Memory", "free -h | grep Mem"),
    ("Uptime", "uptime"),
]


def run_via_sshpass():
    """Run commands via sshpass on the VPS."""
    all_commands = "\n".join(cmd for _, cmd in COMMANDS)
    ssh_cmd = [
        "sshpass", "-p", VPS_PASS,
        "ssh", "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10",
        "-o", "ServerAliveInterval=15",
        f"{VPS_USER}@{VPS_HOST}",
        all_commands,
    ]
    result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=45)
    return result.stdout, result.stderr


def parse_and_report(stdout, stderr):
    """Parse sequential command output and print structured report."""
    lines = stdout.strip().split("\n")
    print("=" * 60)
    print("  VPS HEALTH CHECK — Fabrica EternalL")
    print("=" * 60)

    idx = 0
    for name, _ in COMMANDS:
        print(f"\n{'─' * 40}")
        print(f"  [{name}]")
        print(f"{'─' * 40}")
        # Each command may produce multiple lines
        if idx < len(lines):
            cmd_lines = []
            while idx < len(lines):
                cmd_lines.append(lines[idx])
                idx += 1
                # Heuristic: next command starts after whitespace
                if idx < len(lines) and lines[idx].strip() == "":
                    idx += 1
                    break
            for line in cmd_lines:
                print(f"  {line}")

    if stderr.strip():
        print(f"\n{'─' * 40}")
        print("  [STDERR]")
        print(f"{'─' * 40}")
        for line in stderr.strip().split("\n"):
            print(f"  ! {line}")

    print("\n" + "=" * 60)
    print("  Report complete.")
    print("=" * 60)


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return

    try:
        stdout, stderr = run_via_sshpass()
        parse_and_report(stdout, stderr)

        # Simple health summary
        has_process = "NO_HERMES_PROCESS" not in stdout
        has_state = "gateway_state" in stdout
        all_up = "Up " in stdout

        print("\n  📊 Health Summary:")
        print(f"    Containers up:  {'✅' if all_up else '❌'}")
        print(f"    Gateway state:  {'✅' if has_state else '❌'}")
        print(f"    Process alive:  {'✅' if has_process else '⚠️  state file may be stale'}")
    except FileNotFoundError:
        print("ERROR: sshpass not found. Install with: scoop install sshpass")
        print("Or use the subagent delegation pattern described in the skill.")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("ERROR: SSH connection timed out. VPS may be unreachable.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: SSH failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()