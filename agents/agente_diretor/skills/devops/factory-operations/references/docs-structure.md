# 📚 Documentação Centralizada — `_factorio/docs/`

A documentação da Fábrica foi consolidada em `_factorio/docs/` com índice numerado:

```
_factorio/docs/
  00_INDEX.md             → Navigation hub (start here)
  01_ARCHITECTURE.md      → 3 layers, stack, 8 areas, worker paradigm
  02_MANUAL_DA_FABRICA.md → Consolidated manual (SSOT)
  03_WORKFLOWS.md         → 5 Trigger.dev templates
  04_TOOLS_AND_MODELS.md  → Providers, costs, cloud alternatives
  05_AGENTS.md            → Agent definitions, skills, SOULs
  06_INFRA.md             → VPS, containers, domains, DBs
  07_GLOSSARIO.md         → Dictionary (Worker vs Agent vs Script)
```

## Separação de responsabilidades

| Conteúdo | Local |
|---|---|
| Documentação da FÁBRICA | `_factorio/docs/` |
| Código e infra | `_factorio/` (trigger/, agents/, docker-compose.yml) |
| Notas pessoais, research, Br4nds | `_brain/` (Obsidian vault) |
| Estado operacional runtime | AgentMemory (VPS) |

## Como atualizar

1. Sempre siga a numeração (00, 01, 02...)
2. Atualize `00_INDEX.md` quando adicionar/remover um doc
3. Archive docs obsoletos em `_archive/` — nunca delete
4. Documentos da FÁBRICA = stack, arquitetura, workflows, agentes
5. Documentos de TERCEIROS = docs de ferramentas externas vão em `tools_ref/`