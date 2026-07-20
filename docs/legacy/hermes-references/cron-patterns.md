# Cron Patterns — 24/7 Proactive Monitoring

Standard schedule for the Diretor VPS instance running on Discord gateway.

## Daily Schedule (America/Sao_Paulo)

| Time | Job | Action | Report to |
|------|-----|--------|-----------|
| 🌅 06:00 | **Pulse Matinal** | Check AgentMemory for state, query Teable tasks, identify bottlenecks and opportunities | #diretor |
| 📋 08:00 | **Relatório Diário** | Scan all 8 areas, check weekly progress, save snapshot to AgentMemory | #diretor |
| 🔄 14:00 | **Checkpoint Vespertino** | What was done since morning? Anything blocked? Save to AgentMemory | #diretor |
| 🌙 19:00 | **Checkpoint Noturno** | Day summary, suggestions for tomorrow, save to AgentMemory | #diretor |

## Prompt Pattern

Each cron prompt should follow this structure:

```
1. Connect to AgentMemory and retrieve current factory state
2. Query Teable tasks table for pending/in-progress/done items
3. Identify bottlenecks (tasks stalled >24h, projects with many pending)
4. Identify opportunities (tasks ready to be started, next pipeline steps)
5. If urgent: post alert to #alertas channel
6. Post structured summary
7. Save snapshot to AgentMemory with tag fabrica:estado
```

## Delivery Format

```
discord:<server_id>:<channel_name>
```

Example: `discord:1481006974068854786:geral`

## Hermes Config Entry

```yaml
cron:
  jobs:
    job-name:
      schedule: "0 6 * * *"
      prompt: "Full prompt text here"
      deliver: "discord:1481006974068854786:channel_name"
```