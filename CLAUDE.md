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
3. **Estado no banco** (Teable/D1), nunca na conversa. Coordenação multi-sessão = TASKS no Teable.
4. **Organize por artefato.** Organograma/squad é mapa pra descobrir SOPs, nunca arquitetura de runtime.
5. **Orquestrador magro, executor gordo.** trigger.dev só agenda/retry/observa; compute pesado mora em container (VPS/RunPods). Pasta nova só com demanda (regra de dois).

## Mapa de casas

| Dado | Casa | Acesso |
|---|---|---|
| Narrativa de negócio | Notion (front door, manual) | superfície única humanos+agentes; back-end = Teable/R2/git |
| Estado operacional | Teable | API REST — nunca SQL bruto (conserto da `tasks`: F1.6) |
| Código, SOPs, docs técnicos | este repo (git) | nativo |
| Produto em produção | D1/Workers | repos dos apps |
| Assets binários | R2 / MinIO | S3 API (`scripts/`) |
| Credenciais | `.env` | NUNCA commitar; CRLF → `tr -d '\r'` |

## Skills (SOPs executáveis)

Catálogo em `.claude/skills/` (índice: `.claude/skills/README.md`). Toda skill tem: **(a)** gatilho/inputs, **(b)** passo a passo, **(c)** checklist de pronto (DoD) com verificação real, **(d)** nível de confiança 🟡→🟠→🟢 (promoção = 3 execuções limpas consecutivas). Criar skill nova = `/nova-skill`.

## Regras vivas

- Nada é "pronto" sem verificação real (rodar, medir, conferir — nunca "deve funcionar").
- Sessão que aprende algo atualiza skill/doc na hora (passo 8 do ciclo — o mais importante da fábrica).
- Handoff entre frentes = doc + task, nunca combinado verbal (`/handoff-frente`).
- Gates humanos permanentes: dinheiro · campanha/budget · publicação externa · deleção de dados · credenciais.
- "Não minta, não tenha vergonha de falar a real, Deus abençoe."
