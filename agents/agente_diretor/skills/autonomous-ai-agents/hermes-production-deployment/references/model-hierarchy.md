# Model Hierarchy — Fábrica EternalL

Two distinct categories of model usage:

## 🤖 WORKERS (scripts, pipelines, batch tasks)
Small, fast, cheap models for deterministic work.

| Model | Params | Use Case | Cost |
|-------|--------|----------|------|
| Llama 3.1 8B (via Groq/OpenRouter) | 8B | Text cleaning, structuring, formatting | Near zero (free tier) |

**Characteristics:** High throughput (8+ concurrent threads), preserves original text, does not rewrite/translate.

## 🧠 AGENTS (decision, orchestration, reasoning)
Larger models selected by task complexity.

| Priority | Model | Agentic Index | Cost /M tok | Use |
|----------|-------|---------------|-------------|-----|
| 🥇 80% | DeepSeek V4 Flash | 31.1 | $0.13 | Light agent tasks |
| 🥈 15% | GLM 5.2 (Z.ai) | 43.1 | $1.40 | Medium complexity |
| 🥉 4% | GPT-5.4 | 41.1 | $2.50 | Heavy reasoning |
| ⛔ 1% | Claude Opus/Sonnet | 44+ | $5+ | Emergency fallback only |

**Default for Discord gateway:** DeepSeek V4 Flash (cheapest viable option).

## OpenRouter MCP Tools Available
Connected via MCP server at `https://mcp.openrouter.ai/mcp`:
- `chat-send` — call any model with fallback
- `models-list` — browse catalog with pricing
- `benchmarks` — compare agentic/coding/intelligence scores
- `credits-get` — check balance
- `model-endpoints` — see which providers serve a model
- `rankings-daily` — trending models by volume