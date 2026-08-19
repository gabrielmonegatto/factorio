# 🧭 STACK.md — Infraestrutura da fábrica (EternalL)

> **Reescrito em 19/08/2026** (item 1.8 do roadmap, feito junto com a unificação de dados).
> A versão anterior descrevia a era 1.0 (AgentMemory, multi-bot Discord, Teable como banco corporativo)
> e **continha credenciais em texto plano** — removidas nesta reescrita, ver §6.

---

## 1. O desenho em uma tela

```
JULGAMENTO      Claude Code (sessões por frente)            → constrói e supervisiona
   │
CADÊNCIA        cron na VPS + health check no #fabrica      → dispara esteira
   │
ESTEIRA         script idempotente + fila no D1             → produz volume
   │
COMPUTE         VPS Hetzner (render, TTS) · RunPods (lote)  → músculo
   │
DADO            D1 (estado) · R2 (binário) · git (código)   → casa canônica
   │
VITRINE         Notion (hoje) → BI próprio (fim de 2026)    → onde o Gabriel enxerga
```

## 2. VPS (Hetzner CX53, `167.233.236.209`)

16 vCPU / 32 GB / 320 GB, Falkenstein, ~€35/mês. Acesso por chave `id_ed25519_factorio`.
Papel: **músculo, não banco.** Depois da unificação de 19/08 ela não hospeda mais dado canônico.

| Serviço | O que é | Estado |
|---|---|---|
| `factory-producer.service` (systemd) | Render dos vídeos longos, roda 24/7 consumindo fila | ✅ ativo |
| `/etc/cron.d/factory` | Agendador diário do YouTube (06:00 UTC) | ⏸️ pausado pelo incidente I1 |
| Kokoro TTS (container) | Narração das vozes EN | ✅ ativo |
| Caddy | Proxy reverso + TLS | ✅ ativo |
| Rebuild noturno do BI Br4nds | Gera os dados do `bi.br4nds.com.br` | ✅ ativo |
| ~~Teable + Postgres~~ | Banco tabular self-hosted | ❌ aposentado 19/08 (§5) |
| ~~Outline + MinIO~~ | Wiki self-hosted | ❌ removido 23/07 |
| ~~factorio_agents, agent_memory, mcp_universal~~ | Era Hermes | 🧊 a congelar (roadmap 2.3) |

VPS antiga da Hostinger (`187.127.44.153`) segue no ar sem papel: derrubar (backlog).

## 3. Cloudflare (conta Eternall `dca6b1af…`)

| Recurso | Nomes | Papel |
|---|---|---|
| **D1** | `mananciall-db` · `mananciall-mining` · `eternall-intel` · `mananciallbible` · `br4nds` · `lifesystem` | Todo o estado da máquina (detalhe em `03_DATA_ARCHITECTURE.md` §1) |
| **R2** | `mananciall` (assets do produto) · `channels` (assets de canal) · `eternall-archives` (backup e arquivo morto) | Binários |
| **Workers** | `mananciall.org` (site, SSR Astro) · redirect `/go` (funil) | Produto em produção |
| **Vectorize / KV** | busca semântica · sessões | Apoio do produto |

Gotchas de conta: a credencial enxerga 4 contas, então **sempre exportar `CLOUDFLARE_ACCOUNT_ID`** antes de `wrangler`. Anexar domínio a Worker exige DNS limpo (erro 100117 se houver A/CNAME anterior).

## 4. Serviços externos

| Serviço | Para quê | Nota |
|---|---|---|
| Notion | Vitrine de gestão (Áreas, Roadmap, Tasks, Biblioteca) | Integração "factorio"; só enxerga o que foi compartilhado com ela |
| YouTube Data API | Publicação e métricas dos canais | App **em produção** (em "Testing" o refresh token morre em 7 dias) |
| Paddle / Asaas | Checkout USD / Pix | Ambos em produção, travados em aprovação de conta |
| AssemblyAI | Transcrição word-level | Alternativa avaliada: Groq (backlog) |
| OpenRouter / Anthropic / Gemini | LLM-função das esteiras | Modelo de volume nas tarefas repetitivas |
| RunPods | Render em lote (GPU/CPU) | Só com fila; nunca ligado à toa |
| Resend | E-mail transacional | |
| Hetzner | VPS | |

## 5. O que saiu da stack (e a lição)

| Peça | Morte | Lição que fica |
|---|---|---|
| Outline | 23/07/2026 | Ferramenta de conhecimento sem database-in-doc gera fricção humana; a superfície única venceu |
| **Teable** | **19/08/2026** | Serviço self-hosted que duplica papel de gerenciado vira dívida: cert vencido, tabela quebrada por schema criado fora da API, paginação travando em 1.001 linhas |
| **trigger.dev** | **19/08/2026** | Orquestrador que ninguém usa é peso: cron + fila no D1 já dava retry e observabilidade |
| AgentMemory / Hermes | 07/2026 | O ativo é o arquivo, não o agente |

Regra derivada: **antes de subir container novo, perguntar qual casa existente já resolve.**

## 6. Credenciais

Todas vivem em `_factorio/.env` (nunca commitado; arquivo é CRLF, no bash usar `tr -d '\r'`).

- **Nenhum valor de credencial entra em doc, README, commit ou chat.** Doc cita o NOME da variável.
- Credencial nova tem que **provar identidade**, não só validade (lição do incidente I1: o token do YouTube era válido e publicava no canal errado; hoje `publish_youtube.py` confere `channels?mine=true` contra `EXPECTED_CHANNEL_ID` e aborta se não bater).
- Gate humano permanente: criar, rotacionar ou revogar credencial é sempre do Gabriel.

⚠️ **Dívida aberta em 19/08/2026:** este arquivo continha, em versões anteriores commitadas, o token corporativo do Teable e a chave do AgentMemory (`factorio_secret`). Ambos os serviços estão sendo aposentados, mas o histórico do git guarda os valores — rotacionar/revogar quando desligar. E há uma linha malformada no `.env` (`PADDLE_WEBHOOK_SECRET:` com dois-pontos em vez de `=`), que faz qualquer leitor de `.env` não achar a variável.
