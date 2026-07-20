# 41-Doc Consolidation Findings (Jul 2026)

## Scope

Analyzed all 41 `.md` files in `_brain/projectz/_factorio/docs/` plus ~170 Python/JS
scripts in `scratch/workflows/`. Goal: identify duplicates, stack conflicts, gaps,
and reusable assets.

## Duplicate Groups (~10 files are copies)

| Group | Files | Action |
|-------|-------|--------|
| Setores | `SETORES_FABRICA.md` + `⭐ SETORES_FABRICA.md` | Keep 1 |
| OKRs | `OKRs.md` + `⭐ OKR's.md` | Keep 1 |
| Dicionario | `dicionario_da_fabrica.md` + `⭐ dicionario da fabrica.md` | Keep 1 |
| b4you | `b4you factorio.md` + `b4you_workflow_youtube.md` | Keep the newer one |
| Manual | `MANUAL_DA_FABRICA.md` (V1) + `⭐ MANUAL_DA_FABRICA.md` (V2) | V2 replaces V1 |
| Agentes | `AGENTESMOLDE.md` + `agent.md` | Consolidate |

## Stack Conflicts (critical — need resolution)

| Component | Legacy docs say | Current stack | Who's right |
|-----------|----------------|---------------|-------------|
| Database | Baserow (7 docs) | **Teable** | ✅ Teable |
| Orchestrator | Prefect (4 docs) | **Trigger.dev** | ✅ Trigger.dev |
| LLM gateway | Nemo, Groq | **OpenRouter** | ✅ OpenRouter |

## 3 Critical Gaps

1. **Orchestrator coexistence**: Trigger.dev(TS) vs Prefect(Python) vs Workers Python with `while True` — no document resolves this tension
2. **Dashboard**: Task table exists in Teable but no consolidated UI
3. **I18N pipeline**: Only a conceptual checklist, no implementation

## Docs to Keep (current, no duplicates)

- `⭐ MANUAL_DA_FABRICA.md` — SSOT conceitual
- `factorio_philosophy.md` — 3-layer architecture philosophy
- `⭐ MINERACAO_UNIVERSAL_ARQUITETURA.md` — Mining architecture
- `SPURGEON_VIDEO_SPECS.md` — Video rendering specs
- `README.md` — Tensions and open questions
- `dicionario da fabrica.md` — Conceptual glossary
- `brand_channel_checklist.md` — YouTube channel setup
- `AUTOMAÇÃO - I18N.md` — Internationalization checklist
- `hermes_agent_247_setup.md` — Free-tier setup guide
- `hermes_como_construir_agentes.md` — Agent building tutorial
- `DEPLOY_DIRETOR_VPS.md` + `FINALIZAR_DIRETOR_VPS.md` — VPS deploy
- `b4you_workflow_youtube.md` — YouTube pipeline (kept over duplicate)