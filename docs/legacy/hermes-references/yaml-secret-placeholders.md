# YAML Secret Placeholder Pattern

## The Problem

Hermes redacts secrets in tool output AND in written files. When you write a config.yaml with `echo` or `printf` containing `Bearer <real_secret>`, the output shows `Bearer ***` and the file also gets `Bearer ***` literally.

```yaml
# ❌ This is what gets written when you echo a secret
mcp_servers:
  agentmemory:
    headers:
      Authorization: Bearer ***   # literal asterisks!
```

## The Solution: Placeholder + Sed Replacement

### Step 1: Use placeholders in the template file

```yaml
# ✅ SKILL.md template has placeholders
mcp_servers:
  agentmemory:
    url: http://factorio_agent_memory:3111/mcp
    headers:
      Authorization: "__AGENTMEMORY_SECRET__"
    timeout: 180
```

### Step 2: Deploy script replaces placeholders with real values

```bash
# Deploy script replaces placeholder before SCP to VPS
sed -i "s|__AGENTMEMORY_SECRET__|${REAL_SECRET}|g" config.yaml
sed -i "s|__OPENROUTER_API_KEY__|${OPENROUTER_KEY}|g" config.yaml
```

Or use a `.tfvars`/`.json` file pattern:

```json
// secrets.json — kept locally, never in git
{
  "agentmemory_secret": "factorio_secret",
  "openrouter_key": "sk-or-...",
  "discord_token": "MTQ5Nj..."
}
```

Then a Python script reads from it and does the replacement:

```python
import json, re

with open("secrets.json") as f:
    secrets = json.load(f)

with open("config.yaml") as f:
    content = f.read()

for key, value in secrets.items():
    placeholder = f"__{key.upper()}__"
    content = content.replace(placeholder, value)

with open("config.yaml", "w") as f:
    f.write(content)
```

## Why Hermes Redacts

Hermes uses a built-in secret redactor that scans tool output for patterns like:
- `sk-...` (OpenAI/OpenRouter keys)
- `ghp_...` (GitHub tokens)
- `Bearer <token>`
- `key=`, `token=`, `password=`, `secret=` patterns
- `***` patterns

This is a security feature — it prevents the LLM from seeing raw credentials in tool output. But it means you **cannot** write secrets to files from within Hermes tool calls. Always use a deploy script (PowerShell, bash, Python) that runs outside of Hermes to inject real secrets.

## References

- Hermes docs: `security.redact_secrets` config option
- Set `hermes config set security.redact_secrets false` to disable (NOT recommended for normal use)