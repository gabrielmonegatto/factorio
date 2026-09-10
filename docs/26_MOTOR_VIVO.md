# 26 — Motor vivo: Claude na VPS, tarefas, organograma e sessão remota

> Sessão de pensamento de 10/09/2026. Pergunta do Gabriel: "como eu paro de operar
> na mão pelos chats e começo a trabalhar NA fábrica?" Este doc responde as 5
> perguntas dele, registra o que a pesquisa (docs oficiais + comunidade) mostrou,
> e fecha num plano 80/20 pra hoje. Fontes no §7.

---

## 0. O diagnóstico em 5 linhas

1. **O motor já existe e está desligado.** `infra/diretor/diretor.sh` (cron 07h/17h BRT)
   + `vigia.sh` (a cada 10 min, zero LLM) + fila no banco Tasks do Notion
   (contrato Gate/Prompt/Exec) + skill `/diretor-diario`. Log da VPS: "sem token,
   cadência dormindo" duas vezes por dia desde 01/09. Dez dias parado por um
   arquivo de 1 linha (`/srv/fabrica/.diretor.env`).
2. **Há 2 tasks `gate=auto` esperando** (prova de vida + cookie da Bíblia). O vigia
   dispararia o diretor em até 10 min depois do token existir.
3. **A VPS está ociosa:** load 0.00, 29 GB livres, Claude Code 2.1.258 instalado.
4. **O caminho oficial pra Max em servidor é o que já foi montado:** binário
   oficial + `claude setup-token` + `CLAUDE_CODE_OAUTH_TOKEN`. Permitido por escrito.
5. **Bot no Discord é plugin oficial** (`discord@claude-plugins-official`), com
   pareamento, allowlist e relay de permissão pelo chat. Falta só instalar.

---

## 1. Claude na VPS "24/7" por cron, webhook etc.

**Modelo mental certo:** não é um agente acordado 24h. É um agente **dormente**
que acorda por gatilho, gasta o mínimo e para. Quem tenta "24/7 de verdade" no
Max estoura a janela de 5h e o limite semanal. É exatamente o desenho do vigia.

**Como autentica (oficial):** `claude setup-token` no PC do Gabriel (login no
browser, token OAuth de 1 ano) → `CLAUDE_CODE_OAUTH_TOKEN=...` no servidor. Texto
legal da Anthropic: nada impede "an end user from signing in to the unmodified
Claude Code binary with their own Claude subscription, including where a platform
hosts Claude Code". Custo marginal zero, consome a cota do Max.

**Os 3 gatilhos e como cada um vira trabalho:**

| Gatilho | Como | Estado atual |
|---|---|---|
| Cron | `claude -p "/skill"` com `--allowedTools`, `--permission-mode`, `--max-turns`, `timeout` | diretor.sh, falta `--max-turns`/`timeout`/`--model` |
| "Webhook" | qualquer coisa escreve task na fila (`fila.mjs --criar`); vigia de 10 min dispara | pronto (vigia + `--criar` já commitados) |
| Webhook real (segundos) | Worker Cloudflare recebe HTTP → `--criar` na fila. Se precisar latência de segundos, o Worker bate num endpoint mínimo na VPS que roda `flock diretor.sh` | não precisa hoje |

**Gotchas verificados:**
- `ANTHROPIC_API_KEY` presente no ambiente **vence silenciosamente** o token OAuth
  e passa a cobrar API. O `.env` da fábrica TEM essa chave. O diretor.sh só carrega
  `.diretor.env`, então está protegido; qualquer script novo que faça `source .env`
  antes de chamar `claude` quebra isso. Regra: chamar `claude` sempre com ambiente
  limpo (`env -i` ou só o `.diretor.env`).
- `--bare` (modo recomendado pra scripts) **não lê OAuth**, exige API key. Não usar.
- Limite semanal do Max cai ~17% em 14/09 (fim da promoção +50%, vira +25%).
- Bug de abril (já corrigido e reembolsado): "hermes.md" ou "OpenClaw" no contexto
  jogava a conta em extra usage. O repo tem `docs/legacy/hermes-references/`.
  Risco baixo hoje; registrado pra caso apareça cobrança estranha.
- Routines (nuvem da Anthropic, cron mínimo 1h, cap diário de runs) funcionam
  com Max, mas rodam fora da VPS: não alcançam D1 com segredo, R2, systemd. Servem
  pra tarefa só-de-repo (review de PR, relatório de git). Não é o motor.

## 2. Agent SDK ou assinatura Max?

**Max + binário oficial, sem discussão, pro motor da fábrica.**

| | CLI headless (`claude -p`) | Agent SDK (Python/TS) |
|---|---|---|
| Auth | OAuth do Max (setup-token) | API key (pay-per-token). Política oficial manda devs usarem API key; uso do SDK na assinatura "continua contando na cota" mas a mudança pra crédito separado foi anunciada e pausada em 16/06: zona instável |
| Custo | dentro do plano | relato típico: workload de $200/mês em Max virou $1.000+ em API |
| Skills, CLAUDE.md, subagents, hooks, MCP | nativos | você reimplementa ou passa por opções |
| Quando faz sentido | motor, cadências, sessão remota | embutir um agente DENTRO de um produto vendido (feature pros usuários do app) |

Até o Paperclip, que é o "control plane" mais adotado, no adapter `claude_local`
faz exatamente isso: spawna o binário `claude` com `--resume`. Ninguém sério
monta motor pessoal em SDK pagando token quando tem Max.

## 3. Controle de tarefas

O que a comunidade convergiu (GitHub Issues, Linear, TASKS.md, Paperclip) é o
mesmo desenho que a fábrica já tem: **fila com estado terminal, um processo por
item, teto de turnos, lock, log de custo**. A fila no banco Tasks do Notion com
Gate/Prompt/Exec cumpre isso. O que falta é operacional, não arquitetural:

1. **Ligar** (token). Sem isso tudo o resto é teoria.
2. **Entrada rápida de task.** Hoje criar task exige abrir o Notion e escrever um
   Prompt autocontido. Com a sessão do Discord (§5), "enfileira: X" vira
   `fila.mjs --criar` na hora, do celular.
3. **Freios no comando:** `--max-turns 60`, `timeout 30m`, `--model sonnet`
   (Opus só com o Gabriel na conversa). A skill limita 3 tasks/15 min por
   convenção; o processo precisa do limite duro.
4. **Prova de vida visível:** ao fim de cada cadência, o script manda 3 linhas
   pro Discord por webhook (curl, zero LLM): executadas / travadas / esperando.
   Hoje o relatório fica commitado em `relatorios/` e ninguém lê.
5. **Vigia de cota:** antes de disparar, pular se o uso da conta passar de 80%
   (padrão do `claude-tasks`). Segunda onda; primeiro medir quanto o diretor gasta.

**Paperclip?** É o organograma-como-produto (empresas, cargos, heartbeats,
approvals, budget). Bom, 80k estrelas, adapter pro Claude local. Mas seria um
SEGUNDO plano de controle humano ao lado do Notion, contra a decisão de 03/09
(cânone de 16 bancos, Notion = vitrine humana). Gatilho pra reconsiderar: quando
houver 3+ agentes com papéis distintos rodando por heartbeat e o Notion virar
gargalo. Não é hoje.

## 4. Organograma: agentes por função

Fundamento 4 da constituição continua valendo: organograma é mapa pra achar SOP,
não arquitetura de runtime. O padrão que emergiu na comunidade confirma: **um
papel = persona + diretório de skills + modelo dimensionado**, acordado por
heartbeat, dormindo entre eles. Dentro do Claude Code isso é nativo:

- `.claude/agents/<papel>.md` (subagent): frontmatter com `description`, `tools`,
  `model`, e o corpo com missão + território + skills que pode usar.
- O diretor (orquestrador magro) lê a coluna **Área** da task e delega pro
  subagent da área. Sessão interativa também pode chamar `/frente <área>` ou
  `claude --agent <papel>`.

**Seed proposto (7 áreas do doc 16 §6):** `organizacao`, `int-mercado`,
`int-negocio`, `mineracao`, `content`, `productz`, `i18n`. Cada arquivo com ≤40
linhas: missão (copiada do 16), território de arquivos (o que pode editar),
skills permitidas, gates que trava, modelo (`sonnet`). O executor gordo é a
skill; o agente só carrega o contexto certo. Começar pelos 2 que têm task na
fila hoje (Productz e Organização) e criar os outros quando a primeira task da
área aparecer (regra de dois).

## 5. Sessão remota: bot no Discord na VPS

**Plugin oficial da Anthropic** (`external_plugins/discord`, research preview
desde 20/03/2026), já baixado no marketplace local do PC:

- Roda como MCP server dentro de uma sessão **interativa** do Claude Code:
  `claude --channels plugin:discord@claude-plugins-official`. Precisa de Bun.
- Mensagem no Discord chega como `<channel source="discord">`; o Claude responde
  pelo tool `reply` (também `react`, `edit_message`, `fetch_messages`,
  `download_attachment`, anexos até 25 MB).
- Segurança: pareamento por código de 6 caracteres na primeira DM, depois
  `allowlist` por snowflake; canais de servidor são opt-in por ID; **prompts de
  permissão são relayados pro Discord** e você aprova respondendo `yes <código>`.
- Limitação: 1 sessão = 1 contexto. Se a sessão cair, mensagens não chegam até
  reiniciar. Solução: `systemd` service em `/srv/fabrica` (tmux serve, systemd
  reinicia sozinho).

**O que essa sessão faz pela fábrica:** (a) tira dúvida e mede estado do celular
("como tá o Spurgeon?" → roda health_check); (b) enfileira task com
`--criar`; (c) roda uma skill sob supervisão; (d) recebe as notificações do
diretor (webhook no mesmo canal). Não substitui o diretor (que é headless e
orçado); é a mesa de controle.

Alternativa mais simples pra "só quero mexer do celular": `claude --remote-control`
e usar o app do Claude. Zero setup de bot, mas sem notificações de cron e sem
canal compartilhado. O Discord ganha porque também é o painel de avisos.

**Descartados:** OpenClaw (355k estrelas, mas releases quebrando, 6 CVEs, skills
maliciosas, e a saga de bans de abril), Hermes Agent da Nous (só API key ou
OpenRouter, não usa o Max), NanoClaw (bom, mas é outro harness pra manter).

## 6. Plano 80/20 pra hoje

Ordem é por desbloqueio. Cada item tem gate e tempo.

| # | O quê | Quem | Tempo | Resultado verificável |
|---|---|---|---|---|
| 1 | `claude setup-token` no PC, gravar `CLAUDE_CODE_OAUTH_TOKEN=` em `/srv/fabrica/.diretor.env` (chmod 600) | **Gabriel** (gate credencial) | 3 min | próximo vigia (≤10 min) dispara; task "prova de vida" vira Finalizado no Notion com Exec preenchido |
| 2 | Freios no `diretor.sh`: `--max-turns 60`, `timeout 30m`, `--model sonnet`, ambiente limpo; webhook Discord com o resumo ao fim; registrar no doc 18 | Claude | 30 min | log mostra exit code e custo; mensagem chega no canal |
| 3 | Bot Discord: app no Developer Portal (Message Content Intent, token) | **Gabriel** (gate credencial) | 10 min | token em `~/.claude/channels/discord/.env` na VPS |
| 4 | Instalar Bun + plugin na VPS, `fabrica-chat.service` (systemd, `/srv/fabrica`), parear, allowlist, canal `#fabrica` opt-in | Claude | 45 min | DM "status" recebe resposta com número medido do health_check |
| 5 | Seeds de organograma: `.claude/agents/productz.md` e `organizacao.md`; diretor delega por Área | Claude | 40 min | task da Bíblia executada pelo agente productz, com nota no Exec |
| 6 | Atualizar `04_ROADMAP`/`18_AUTOMACOES`, memória, commit | Claude | 10 min | git limpo |

Fica pra depois (com gatilho): vigia de cota (>80% pula) depois de medir 1
semana; Routines pra review de PR dos apps; Paperclip só com 3+ papéis vivos;
Agent SDK só se um produto precisar de agente embutido.

## 7. Fontes

Oficiais: [Headless](https://code.claude.com/docs/en/headless) ·
[Authentication](https://code.claude.com/docs/en/authentication) ·
[Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance) ·
[Channels](https://code.claude.com/docs/en/channels) ·
[Routines](https://code.claude.com/docs/en/routines) ·
[Sub-agents](https://code.claude.com/docs/en/sub-agents) ·
[Agent SDK com plano (Help Center)](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan) ·
[Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview).

Comunidade: [Paperclip](https://github.com/paperclipai/paperclip) ·
[OpenAI Symphony (spec)](https://github.com/openai/symphony) ·
[cdcttr/scale](https://github.com/cdcttr/scale) ·
[NanoClaw](https://github.com/qwibitai/nanoclaw) ·
[Okhlopkov, always-on agent server](https://okhlopkov.com/always-on-ai-agent-server-setup/) ·
[Product Compass, Claude Code em VPS](https://www.productcompass.pm/p/claude-code-vps) ·
[Whoff Agents, custo solo builder](https://dev.to/whoffagents/claude-managed-agents-vs-running-your-own-a-solo-builders-cost-breakdown-35db) ·
[linha do tempo dos bans, HN](https://news.ycombinator.com/item?id=47844269) ·
[corte de 17% em 14/09](https://explainx.ai/blog/anthropic-claude-code-limits-17-percent-cut-september-2026-august-2026).
