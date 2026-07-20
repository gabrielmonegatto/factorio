# 🕯️ LEGACY TRANSITION — APOSENTADORIA DA CAMADA DE AGENTES

> Peça por peça: por que existiu, por que não precisa mais, o que substitui, como congelar.
> ⚠️ **NADA AQUI FOI EXECUTADO AINDA.** Execução é a Fase 2 do roadmap, após martelo M3.
> Princípio: **congelar, não destruir** — containers param, volumes ficam, tudo reversível.

---

## 1. O quadro geral

A camada de agentes 1.0 existia pra suprir uma carência: julgamento contínuo com modelo barato. Cada peça era um contorno dessa limitação. Com o QG (Claude Code/Max), o julgamento vem de sessões com harness completo — e cada contorno perde a razão de existir. O que sobra de valor em cada peça é destilado antes do congelamento.

## 2. Peça por peça

### `factorio_agents` — Hermes (agente_diretor) + agentes Python

> ⚠️ **ATENÇÃO (descoberto na auditoria de 18/07):** este container NÃO é 100% legado — o **Kokoro TTS roda dentro dele** na VPS (ver `agents/agente_diretor/skills/devops/factory-operations/references/tts-deployment.md`) e serve a esteira de narração do Spurgeon. **NÃO congelar antes de realocar o Kokoro** (pra um container próprio `factorio_tts` enxuto, ou pra RunPods CPU). O freeze deste container fica CONDICIONADO à realocação do TTS.

| | |
|---|---|
| **Por que existiu** | "Cérebro" 24/7 pra supervisionar esteiras, rodar crons de análise e receber webhooks; agentes de mineração/produto pra trabalho pesado |
| **Por que não precisa** | O papel de Diretor é EXATAMENTE o que uma sessão de rotina faz melhor (lê Teable/D1/Meta → decide → escreve briefing → aciona esteira), com auditoria em git e capacidade de consertar as próprias ferramentas. Os crons viram sessões agendadas. O webhook do Baserow morreu com o Baserow |
| **O que substitui** | Skill `/diretor-diario` + sessões de rotina (Fase 1). O Kokoro TTS ganha casa própria (container dedicado ou RunPods) ANTES do freeze |
| **Destilar antes** | **1º: realocar Kokoro TTS** · scrapers/ETL úteis de `agents/agente_minerador`, `agente_produto`, `agente_analisador_funil` → `_factorio/scripts/` · aprendizados de `agents/skills/` e `agents/agente_diretor/skills/` → absorver nos docs/skills novos |
| **Congelar** | Só após realocação do TTS: `docker compose stop factorio_agents` (imagem e volumes ficam) |

### `agent_memory` — AgentMemory (memória semântica)

| | |
|---|---|
| **Por que existiu** | Agentes fracos e sem contexto persistente precisavam de um "lembrete" semântico entre execuções |
| **Por que não precisa** | Memória que importa precisa ser **legível, curada e auditável** — por humano e por máquina. Na prática, a wiki versionada venceu a busca vetorial: decisão vai pro Outline, estado vai pro Teable, convenção vai pro git. Busca semântica sobre fatos soltos não paga o serviço que a mantém |
| **O que substitui** | Outline (narrativa) + Teable (estado) + git (código/convenções) + memória de arquivos do próprio Claude Code |
| **Destilar antes** | Exportar memórias via API (`factorio_secret`) → doc "Memórias herdadas do AgentMemory" no Outline Holding; revisar e distribuir o que ainda vale |
| **Congelar** | `docker compose stop agent_memory` (volumes `agent_memory_*` ficam) |

### `mcp_universal` — MCP server caseiro

| | |
|---|---|
| **Por que existiu** | Expor Baserow/banco/LLM como ferramentas pros agentes Python |
| **Por que não precisa** | Claude Code conecta MCPs oficiais/diretos por serviço (trigger.dev oficial já conectado; Teable e Outline via REST/MCP dedicado). Um proxy universal caseiro é mais uma peça pra manter, sem ganho |
| **O que substitui** | Config de MCP do Claude Code por serviço (Fase 1.4/1.5) |
| **Congelar** | `docker compose stop mcp_universal` |

### `factorio_redis` — Redis "geral"

| | |
|---|---|
| **Por que existiu** | Fila/cache da camada de agentes |
| **Por que não precisa** | Morre junto com os consumidores. ⚠️ **NÃO confundir** com `factorio_teable_cache` (Redis do Teable — FICA) e `outline_redis` (FICA) |
| **Congelar** | Verificar que nenhum serviço vivo aponta pra ele → `docker compose stop redis` |

### Multi-bot Discord (gateway por agente)

| | |
|---|---|
| **Por que existiu** | Cada agente precisava do próprio token/gateway (session conflict documentado no STACK.md) |
| **Por que não precisa** | Sem frota, sem gateway. Notificação não precisa de bot conectado — webhook resolve |
| **O que substitui** | 1 webhook no canal #fabrica (Fase 1.3). Conversa com Claude = Claude Code. Bridge conversacional no Discord = projeto futuro OPCIONAL (Agent SDK), só se sentir falta |
| **Congelar** | Arquivar/revogar tokens dos bots no Developer Portal (guardar registro no .env comentado) |

## 3. O que FICA na VPS (a fábrica enxuta)

| Container | Papel |
|---|---|
| `factorio_proxy` (Caddy) | SSL + roteamento dos subdomínios |
| `factorio_teable` + `factorio_teable_db` + `factorio_teable_cache` (+ job `teable-db-migrate`) | Dados operacionais |
| `outline_holding` + `outline_br4nds` + `outline_db` + `outline_redis` | O "Notion" da holding |
| `outline_minio` (+ job `outline_minio_setup`) | Anexos do Outline |

De ~14 containers para ~10, todos com papel claro. Pós-freeze (Fase 2): limpar rotas mortas do Caddyfile (`agents.`, `memory.`, `memory-viewer.`, `mcp.`) e atualizar `STACK.md` + `_factorio/README.md`.

## 4. Critério de reversão

Se em até 30 dias algo fizer falta real: `docker compose start <serviço>` traz de volta em segundos (volumes intactos). Se nada fez falta em 30 dias: manter congelado por mais 60 e só então discutir remoção definitiva (com backup dos volumes antes). Pressa zero em deletar.
