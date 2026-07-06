---
name: system-reconnaissance
description: "Methodically explore unfamiliar systems — databases, APIs, services, directories — without jumping to conclusions."
version: 1.1.0
author: Diretor de Operações / EternalL
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [reconnaissance, discovery, exploration, teable, database, triage]
    related_skills: [systematic-debugging]
---

# System Reconnaissance

## Overview

When asked to "take a look at" an unfamiliar system (database, API, service, directory), resist the urge to consolidate, conclude, or propose actions immediately. The goal is **exploration first, understanding second, action third.**

## User's Preferred Flow (learned from experience)

1. **Ask ONE question at a time.** NEVER dump 3+ questions at once. The user will say "eai ta dificil ein". Ask one, get the answer, then ask the next. Iterative beats exhaustive.
2. **Do first, explain later.** Explore the system, report findings concisely, then ask ONE clarifying question.
3. **Be aggressive about pruning.** When triaging documentation, classify ruthlessly: keep only what's core, archive the rest. "Muita coisa velha" causes hallucinations in other agents.
4. **Never consolidate before understanding the full picture.** The user will tell you when you're ready to consolidate. If you propose consolidating too early, they'll say "nao consolide nada ainda — vc ainda nao pegou a visão total da parada".
5. **When the user says "pelo amor, veja isso aqui" followed by a link — DROP EVERYTHING.** This is an URGENT redirect signal. Do not finish your current thought, do not wrap up, do not say "antes de continuar". Open the link immediately. The user has found something they consider critical and wants your reaction NOW.

## Step-by-Step Reconnaissance

### Phase 1 — Surface Scan

Find ALL entry points before diving deep:

```bash
# 1. Check env files for connection strings
find . -name ".env*" -not -path "./node_modules/*" 2>/dev/null | head -20

# 2. Check for existing scripts/inspection tools
find . -name "*inspect*" -o -name "*list_*" -o -name "*check_*" 2>/dev/null | grep -v node_modules | head -20

# 3. Check for config docs
find . -name "AGENTS.md" -o -name "CLAUDE.md" -o -name "README.md" 2>/dev/null | grep -v node_modules | head -10
```

### Phase 2 — Connect & Map

Try connection methods in order (fastest → most reliable):

1. **Existing scripts first** — If scripts exist for inspection (`list_teable_bases.py`, `check_teable_*.py`), run them first.
2. **REST API** — If not, try the REST API. Check `.env` for URL + token.
3. **Direct DB** — Last resort. Auth may fail, but worth trying.

Always map the FULL landscape before discussing any specific part.

### Phase 3 — Report Findings

Report in this format:

```
## Structure Found
- [System name]: [brief description]
- [Component 1]: [what it does, key fields]
- [Component 2]: [what it does, key fields]

## Questions (ask ONE at a time)
1. [single, precise question]
```

### Pitfalls

- ❌ DON'T ask 5 questions in one message. The user will say "eai ta dificil ein"
- 🚨 **🚨 "Mas pelo amor, veja isso aqui" = URGENT REDIRECT.** When the user says "pelo amor" followed by a link or a new topic, DROP EVERYTHING. Do not finish your current reasoning, do not wrap up, do not say "antes de continuar." The link IS the priority. Open it immediately. This signal overrides whatever you're doing — the user has found something they consider critical and wants your reaction NOW, not after you finish your current thought.
- ❌ DON'T propose consolidation or action before the user agrees you have the full picture
- ❌ DON'T skip env files — they contain the real connection strings
- ❌ DON'T hardcode tokens/passwords in scripts — use separate config files
- ✅ DO try existing scripts first — they exist for a reason
- ✅ DO read at least 3 different source files before forming a conclusion
- ✅ DO report "erro" honestly — fabricated output is worse than a blocker
- ✅ DO look for Docker containers on the target system first — `docker ps --format 'table {{.Names}}\t{{.Status}}'` gives an instant architecture map
- ✅ DO store credentials in separate JSON config files (e.g. `.teable_token.json`, `.agentmemory_secret.json`) and have scripts read from them — this avoids Hermes terminal redaction breaking bash commands when secrets appear in output
- ✅ DO use `write_file` for credential configs, then `terminal` to run Python scripts that read them

### Teable-Specific Reconnaissance

When exploring a Teable instance:

```
# List spaces
curl -s http://localhost:3000/api/space | python -m json.tool

# List bases in a space
curl -s http://localhost:3000/api/space/{space_id}/base | python -m json.tool

# List tables in a base
curl -s http://localhost:3000/api/base/{base_id}/table | python -m json.tool

# List fields in a table
curl -s http://localhost:3000/api/table/{table_id}/field | python -m json.tool
```

Token goes in Authorization header: `Bearer {token}`.

### Concrete Example: EternalL Teable

For the specific EternalL Teable instance (`localhost:3000`), the full base/table/field mapping is documented in `references/teable-mapping.md`. Key facts:
- Base **Eternall** (ID: bseWeczeNfCSaMlu2EC) = the Factory DB (~35 tables)
- `tasks` = SSOT (Task ID, Brand, Project_Slug, area, Status, Projeto, Progresso)
- `content_index` = Project catalog
- `content_chunks` = Content chunks
- `knowledge` = Agent knowledge base
- `agent_journal` = Decision history