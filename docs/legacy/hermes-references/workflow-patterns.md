# Workflow Pattern Analysis (Jul 2026)

Legacy workflow code lives at `scratch/workflows/`. ~170 scripts across 7 projects.
These are battle-tested patterns that can inform the new Trigger.dev-based pipeline.

## Projects Overview

| Project | Scripts | Language | Architecture | Reuse Value |
|---------|---------|----------|-------------|-------------|
| **spurgeon_generator/** | ~50 | Python | Pipeline linear + Workers autonomos | HIGH |
| **youtube_hunter/** | ~30 | Python | Pipeline Prefect | HIGH |
| **motoropus_clipper/** | ~15 | Python | Watchdog + StateGraph multi-agente | HIGH |
| **agent_orchestrator/** | 2 | Python | FileSystem Watcher + Sync | MEDIUM |
| **site_miner/** | 3 | Python | Scraper + Teable Client | HIGH |
| **pixel_perfect/** | 4 | JS | Pipeline c/ checkpoint | MEDIUM |
| **scratch/** | ~80 | Python | One-shot migracao/dedup | LOW |

## 5 Architectural Patterns Identified

### 1. Worker Status-Machine (polling DB)
**Where:** `spurgeon_generator/` — `spurgeon_master_pipeline.py`, `factory_producer.py`  
**Pattern:** Infinite loop polls database for new work items, processes them, updates status.  
**Strengths:** Resilient, no orchestrator needed, self-healing on crash.  
**For new factory:** Workers autonomos ideais para esteiras batch.

### 2. Pipeline Linear (Prefect)
**Where:** `youtube_hunter/` — `hunter_flow.py`, `discovery_flow.py`  
**Pattern:** Sequential DAG stages (discover → classify → dedupe → enrich → seed).  
**Strengths:** Clear stage boundaries, retry per stage, observable.  
**For new factory:** Convert Prefect DAGs to Trigger.dev tasks.

### 3. StateGraph Multi-Agente
**Where:** `motoropus_clipper/` — `squad_langcore.py`  
**Pattern:** LangGraph StateGraph with conditional edges, analyst/clipper/revisor/styler agents as nodes.  
**Strengths:** Dynamic branching per content type, parallel sub-processes.  
**For new factory:** Patterns for multi-agent orchestration.

### 4. Event-Driven (FileSystem Watcher)
**Where:** `agent_orchestrator/` — `watcher.py`  
**Pattern:** watchdog-based file watcher with debounce/cooldown. Triggers actions on file change.  
**Strengths:** Low latency, no polling.  
**For new factory:** Hot-reload config, auto-discovery.

### 5. Pipeline com Checkpoint
**Where:** `pixel_perfect/` — `extract.js`, `qa.js`  
**Pattern:** Stage produces artifact → next stage consumes it. Checkpoint at each stage.  
**Strengths:** Resume from failure, audit trail.  
**For new factory:** Asset production pipeline.

## Top 10 Reusable Assets

| # | Asset | Location | Why |
|---|-------|----------|-----|
| 1 | `teable_client.py` | `site_miner/` | Ready-to-use Teable ORM |
| 2 | `squad_langcore.py` | `motoropus_clipper/` | Multi-agent LangGraph |
| 3 | `services/analyst.py` | `motoropus_clipper/` | Chunking + LLM analysis |
| 4 | `watcher.py` | `agent_orchestrator/` | File watcher w/ cooldown |
| 5 | `extract.js` + `qa.js` | `pixel_perfect/` | Visual extraction + QA |
| 6 | `channel_watchdog_flow.py` | `motoropus_clipper/` | Watchdog schedule |
| 7 | `cleaner.py` (smart_clean) | `spurgeon_generator/` | Hybrid cleaning (regex + LLM) |
| 8 | Dedup por URL pattern | `scratch/` multiple scripts | Consolidado em multi scripts |
| 9 | Prefect flow skeletons | `youtube_hunter/` | Convertivel para Trigger.dev |
| 10 | `database.py` (models) | `motoropus_clipper/` | SQLAlchemy + UUID/JSONB |

## What to Discard

- ~50 one-shot migration scripts in `scratch/` (executed, no reuse)
- Plane.so integration (obsolete)
- Firecrawl (high cost, replace with simpler scraper)
- Hardcoded credentials in any script
- Anything referencing Baserow (migrated to Teable)