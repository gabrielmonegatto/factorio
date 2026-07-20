# SSH Key Auth — VPS Passwordless Access

## Why Key Auth?

The boss will **furious** if you ask for the VPS password interactively. SSH key
auth avoids the Windows password popup entirely. Set it up ONCE and never deal
with it again.

## Setup (one-time)

Run this **after** connecting with password auth via paramiko the first time:

```python
import paramiko, os, subprocess

HOST = "187.127.44.153"
USER = "root"
PWD = ".gmIN&QAY8Q'L9vS"  # password from HANDOFF.md
PORT = 22

# Connect with password the first time
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PWD, timeout=15)

# Generate key pair locally
home = os.path.expanduser("~")
key_path = os.path.join(home, ".ssh", "id_ed25519_factorio")
if not os.path.exists(key_path):
    subprocess.run(["ssh-keygen", "-t", "ed25519", "-f", key_path,
                     "-N", "", "-C", "diretor-fabrica"], capture_output=True)

# Read public key
with open(key_path + ".pub") as f:
    pub_key = f.read().strip()

# Install on VPS
client.exec_command(f"mkdir -p /root/.ssh && chmod 700 /root/.ssh")
client.exec_command(f"echo '{pub_key}' >> /root/.ssh/authorized_keys")
client.exec_command(f"chmod 600 /root/.ssh/authorized_keys")
client.close()
```

## Usage (after setup)

```python
import paramiko, os

HOST = "187.127.44.153"
USER = "root"
PORT = 22
key_path = os.path.join(os.path.expanduser("~"), ".ssh", "id_ed25519_factorio")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=key_path, timeout=15)

def run(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    rc = stdout.channel.recv_exit_status()
    return out, err, rc
```

## Key file location

- **Private key**: `~/.ssh/id_ed25519_factorio` (no passphrase)
- **Public key**: `~/.ssh/id_ed25519_factorio.pub`
- **On VPS**: installed in `/root/.ssh/authorized_keys`

## What NOT to do

- **NEVER ask the user for the password** — they will get angry
- **NEVER use `terminal()` with raw SSH commands** — they trigger interactive
  password prompts that block the session
- **NEVER pipe passwords via stdin** — `sshpass` is usually not installed on
  Windows git-bash, and `sudo -S` with piped passwords is blocked by Hermes

Always use **paramiko Python scripts** (via `write_file` + `terminal` running
the script, or `execute_code`) for VPS operations.