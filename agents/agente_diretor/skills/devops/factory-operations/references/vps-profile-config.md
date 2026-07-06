# VPS Profile Config — Diretor 24/7

Full `diretor-vps/config.yaml` template for the Hermes profile that runs on the VPS.

## Usage

Copy this template, replace placeholders (`__AGENTMEMORY_SECRET__`, `__OPENROUTER_KEY__`, `__DISCORD_TOKEN__`, `__SERVER_ID__`), and place at `~/.hermes/profiles/diretor-vps/config.yaml`.

## Template

```yaml
# Perfil Diretor VPS - Fabrica EternalL

model:
  default: google/gemini-2.5-flash
  provider: openrouter

agent:
  max_turns: 90
  reasoning_effort: medium
  gateway_timeout: 1800

terminal:
  backend: docker

memory:
  memory_enabled: true
  user_profile_enabled: true

gateway:
  discord:
    enabled: true
    require_mention: true
    auto_thread: true
    history_backfill: true
    history_backfill_limit: 50
    reactions: true

mcp_servers:
  agentmemory:
    url: http://factorio_agent_memory:3111/mcp
    headers:
      Authorization: "__AGENTMEMORY_SECRET__"
    timeout: 180
    connect_timeout: 30
  openrouter:
    url: https://mcp.openrouter.ai/mcp
    headers:
      Authorization: "__OPENROUTER_KEY__"
    timeout: 180
    connect_timeout: 30

cron:
  jobs:
    pulse-matinal:
      schedule: "0 6 * * *"
      prompt: >
        Pulse Matinal - Fabrica EternalL. Conecte AgentMemory, veja estado,
        cheque tasks no Teable, identifique gargalos, poste resumo no Discord.
      deliver: "discord:__SERVER_ID__:geral"
    relatorio-diario:
      schedule: "0 8 * * *"
      prompt: >
        Relatorio diario. Consulte 8 areas, progresso da semana,
        salve snapshot no AgentMemory, poste no Discord.
      deliver: "discord:__SERVER_ID__:geral"
    checkpoint-tarde:
      schedule: "0 14 * * *"
      prompt: >
        Checkpoint vespertino. O que foi feito? Algo travado?
        Salve no AgentMemory, poste no Discord.
      deliver: "discord:__SERVER_ID__:geral"
    checkpoint-noite:
      schedule: "0 19 * * *"
      prompt: >
        Checkpoint noturno. Resumo do dia, sessoes para amanha.
        Salve no AgentMemory, poste no Discord.
      deliver: "discord:__SERVER_ID__:geral"
```

## Credential File (`diretor-vps/.env`)

```env
DISCORD_BOT_TOKEN=__DISCORD_TOKEN__
OPENROUTER_API_KEY=__OPENROUTER_KEY__
AGENTMEMORY_SECRET=__AGENTMEMORY_SECRET__
```

## Placeholder Replacement

Use the `yaml-secret-placeholders.md` pattern to replace `__PLACEHOLDERS__` before deploying:

```python
import json

with open("secrets.json") as f:
    secrets = json.load(f)

for yaml_path in ["diretor-vps/config.yaml", "diretor-vps/.env"]:
    with open(yaml_path) as f:
        content = f.read()
    for key, val in secrets.items():
        content = content.replace(f"__{key.upper()}__", val)
    with open(yaml_path, "w") as f:
        f.write(content)
```

With `secrets.json`:
```json
{
  "AGENTMEMORY_SECRET": "factorio_secret",
  "OPENROUTER_KEY": "sk-or-...",
  "DISCORD_TOKEN": "MTQ5Nj...",
  "SERVER_ID": "1481006974068854786"
}
```