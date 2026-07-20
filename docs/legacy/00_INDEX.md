# 🏭 FÁBRICA ETERNALL — ÍNDICE DA DOCUMENTAÇÃO

> Este é o mapa de navegação da Fábrica. Toda documentação vive aqui.
> Última atualização: 08/07/2026

---

## 📂 Estrutura

```
📁 _factorio/docs/
  ├── 📄 00_INDEX.md              ← Você está aqui
  ├── 📄 01_ARCHITECTURE.md       → Stack, 3 camadas, visão geral
  ├── 📄 02_MANUAL_DA_FABRICA.md  → Manual consolidado (SSOT)
  ├── 📄 03_WORKFLOWS.md          → Templates Trigger.dev
  ├── 📄 04_TOOLS_AND_MODELS.md   → Ferramentas e custos
  ├── 📄 05_AGENTS.md             → Agentes, skills, SOULs
  ├── 📄 06_INFRA.md              → VPS, containers, domínios
  └── 📄 07_GLOSSARIO.md          → Dicionário da fábrica
```

## 📋 Documentos por Prioridade

| # | Documento | O que contém | Leitura |
|---|---|---|---|
| 1 | `02_MANUAL_DA_FABRICA.md` | Stack, áreas, 3 camadas, regras, SSOT | ✅ Obrigatória |
| 2 | `01_ARCHITECTURE.md` | Filosofia, CONTENT→INDEX→TASKS, worker paradigm | ✅ Obrigatória |
| 3 | `04_TOOLS_AND_MODELS.md` | LLMs, TTS, custos, provedores, Kokoro na VPS | ✅ Antes de codar |
| 4 | `03_WORKFLOWS.md` | 5 templates Trigger.dev, pipelines | ✅ Antes de codar |
| 5 | `06_INFRA.md` | VPS, 14 containers, 9 domínios, DBs | 🔧 Consulta |
| 6 | `05_AGENTS.md` | Agentes, skills, onboarding | 🔧 Consulta |
| 7 | `07_GLOSSARIO.md` | 3 camadas, worker vs script, filosofia | 🔧 Dúvidas |

## 🔗 Links Rápidos

| Recurso | Link |
|---|---|
| Trigger.dev Dashboard | https://cloud.trigger.dev/projects/v3/proj_dsuhcyzyqgruytusyipj |
| Teable (db) | https://db.markeologia.com.br |
| Outline Holding | https://admin.markeologia.com.br |
| Outline Br4nds | https://admin.br4nds.com.br |
| Hermes Agents | https://agents.markeologia.com.br |
| MinIO Console | https://minio.markeologia.com.br |
| AgentMemory Viewer | https://memory-viewer.markeologia.com.br |

## 🧠 Onde vive cada coisa

| Conteúdo | Local |
|---|---|
| Documentação conceitual | `_factorio/docs/` |
| Código Trigger.dev | `_factorio/trigger/` |
| Agentes | `_factorio/agents/` |
| Infra (docker-compose) | `_factorio/` |
| Handoff operacional | `_factorio/HANDOFF.md` |
| Estado runtime | AgentMemory (VPS) |
| Notas pessoais / research | `_brain/` |