# 🏭 Constituição da Fábrica (Factorio)

Você está no QG da fábrica de negócios digitais da holding EternalL. Este repo é o SUBSOLO: tudo que **constrói e opera** os negócios. Os negócios (frutos) vivem em `../apps/*`, cada um repo próprio — sessão de fábrica não edita lá (regra do terreno).

## Oriente-se (sessão nova lê nesta ordem)

1. `docs/00_INDEX.md` — mapa da documentação
2. `docs/02_OPERATING_MODEL.md` — COMO todo trabalho acontece (ciclo padrão, tipos de sessão, gates)
3. `docs/04_ROADMAP.md` — fase atual e pendências
4. Aprofundamento: visão/decisões em `docs/01_MASTERPLAN.md` · dados em `docs/03_DATA_ARCHITECTURE.md`

## Os 5 fundamentos

1. **Julgamento ≠ execução.** Decisão aberta → sessão Claude com skill · repetitivo com prompt fixo → LLM-função (OpenRouter/Haiku dentro de task) · sem ambiguidade → código puro.
2. **O ativo é o arquivo, não o agente.** Aprendizado vira skill/doc/template na hora — o que fica só na conversa morreu.
3. **Estado no banco** (D1), nunca na conversa. Coordenação multi-sessão = banco Tasks no Notion (visão humana) + fila no D1 (estado de esteira).
4. **Organize por artefato.** Organograma/squad é mapa pra descobrir SOPs, nunca arquitetura de runtime.
5. **Orquestrador magro, executor gordo.** Cadência = cron na VPS com health check; pipeline multi-etapa = script idempotente com fila no D1 (padrão da mineração). Compute pesado mora em container (VPS/RunPods). Pasta nova só com demanda (regra de dois).

## Mapa de casas (unificação de 19/08/2026)

| Dado | Casa | Acesso |
|---|---|---|
| Gestão da fábrica (áreas, roadmap, tasks humanas) | Notion (vitrine; migra pro BI no fim de 2026) | API REST (`tools/notion/`) |
| Estado de esteira, intel, produto | **D1** (`mananciall-db`, `mananciall-mining`, `eternall-intel`, `br4nds`) | API HTTP do D1 (parâmetro vinculado) ou `wrangler` |
| Código, SOPs, docs técnicos | este repo (git) | nativo |
| Assets binários e arquivo morto | R2 (`mananciall`, `channels`, `eternall-archives`) | `wrangler r2` / S3 API |
| Credenciais | `.env` | NUNCA commitar; CRLF → `tr -d '\r'` |

> **Teable APOSENTADO em 19/08/2026** (virou peça avulsa: D1 tomou o papel de estado, Notion o de curadoria). Migração e arquivo: `docs/17_UNIFICACAO_DE_DADOS.md`. **trigger.dev** saiu da stack pelo mesmo motivo: nada em produção usava.

## Skills (SOPs executáveis)

Catálogo em `.claude/skills/` (índice: `.claude/skills/README.md`). Toda skill tem: **(a)** gatilho/inputs, **(b)** passo a passo, **(c)** checklist de pronto (DoD) com verificação real, **(d)** nível de confiança 🟡→🟠→🟢 (promoção = 3 execuções limpas consecutivas). Criar skill nova = `/nova-skill`.

## Regras vivas

- Nada é "pronto" sem verificação real (rodar, medir, conferir — nunca "deve funcionar").
- Sessão que aprende algo atualiza skill/doc na hora (passo 8 do ciclo — o mais importante da fábrica).
- Handoff entre frentes = doc + task, nunca combinado verbal (`/handoff-frente`).
- **Raiz da _factorio não recebe arquivo.** Script nasce em `scripts/`, rascunho em `scratch/` (ignorado), doc em `docs/`. Sessão termina com `git status` limpo: trabalho real commitado na hora, na frente certa (sanitização 07/08/2026 removeu 68 pendências acumuladas; não deixar voltar).
- Gates humanos permanentes: dinheiro · campanha/budget · publicação externa · deleção de dados · credenciais.
- "Não minta, não tenha vergonha de falar a real, Deus abençoe."
