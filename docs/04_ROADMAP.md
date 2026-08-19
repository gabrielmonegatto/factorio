# 🗺️ ROADMAP — FÁBRICA 2.0

> Cada fase tem critério de pronto (DoD) verificável. Não se avança com DoD aberto.
> Atualizado: 18/07/2026.

---

## Fase 0 — Fundação documental ✅ (18/07/2026)

Escrever o desenho completo (estes docs 00–05) com visão, modelo operacional, arquitetura de dados, transição de legado.

**DoD:** Gabriel leu, ajustou o que precisava e aprovou. Martelos em aberto batidos (ver §Decisões em aberto).

## Fase 1 — Núcleo operacional

O mínimo pra fábrica operar no modelo novo:

| # | Entrega | Detalhe |
|---|---|---|
| 1.1 | **CLAUDE.md constituição** ✅ 20/07 | Desenho final (terreno/subsolo/superfície): placa em `EternalL/CLAUDE.md` (herdada por todas as sessões) + constituição em `_factorio/CLAUDE.md`. Sessão de fábrica abre em `_factorio/`. Repo raiz dissolvido (histórico em `Desktop\_archives\eternall-pre-split.git`) |
| 1.2 | **Skills base** 🔶 parcial 20/07 | ✅ `/fabrica`, `/nova-skill`, `/handoff-frente` (🟡 draft em `.claude/skills/`) · ⬜ `/diretor-diario` (depende de 1.4/1.5). Backlog do catálogo completo: `docs/backlog_skills_seed.md` (workflows/agentes/squads por área, destilado do Obsidian) |
| 1.3 | **Webhook de notificação** | Canal #fabrica no Discord (webhook simples, sem bot de gateway) |
| 1.4 | ~~Acesso ao Outline via API~~ | ❌ Cancelado: Outline morto em 23/07/2026. O equivalente vivo é o kit `tools/notion/` (✅ funcionando) |
| 1.5 | ~~Acesso ao Teable via API~~ | ❌ Cancelado 19/08/2026 junto com o Teable. O acesso que importa hoje é D1 (API HTTP com parâmetro vinculado) ✅ |
| 1.6 | ~~🩹 Consertar a tabela `tasks` no Teable~~ | ❌ **CANCELADO 19/08/2026.** Não se conserta o que vai ser aposentado: o Teable inteiro saiu da stack (`03_DATA_ARCHITECTURE.md` §7 e `17_UNIFICACAO_DE_DADOS.md`). O quadro de tarefas humanas virou o banco Tasks do Notion; estado de esteira virou fila no D1. O sintoma (400 Invalid FieldId por campo criado via SQL bruto) fica registrado como lição: **schema criado por fora da API oficial quebra a ferramenta** |
| 1.7 | **Rodar `/diretor-diario` manualmente 3x** | Lê Teable + Outline → escreve briefing no Outline → notifica webhook |
| 1.8 | **Atualizar `_factorio/README.md` e `STACK.md`** | Refletir o desenho novo (hoje descrevem a era anterior) |

**DoD:** 3 execuções limpas e úteis do diretor diário; skills base 🟠; qualquer sessão nova se orienta sozinha só com o CLAUDE.md + docs.

## Fase 2 — Transição do legado (pode rodar em paralelo com a Fase 3)

Executar o `05_LEGACY_TRANSITION.md`:

| # | Entrega |
|---|---|
| 2.1 | ✅ Memórias do AgentMemory destiladas → `docs/legacy/hermes-references/` (20/07) |
| 2.2 | ✅ Código útil dos agentes Python destilado → `scripts/` (20/07) |
| 2.3 | Congelar containers: `factorio_agents`, `agent_memory`, `mcp_universal`, `factorio_redis` (stop, sem apagar volumes) |
| 2.4 | Limpar Caddyfile (rotas mortas) + arquivar tokens dos bots Discord |
| 2.5 | ✅ Backups semanais (D1 + Notion → R2) — `scripts/backup/` (19/08) |
| 2.6 | ✅ Superado: `_wiki` narrativo migrou pro Notion, não pro Outline (que morreu) |
| 2.7 | **Aposentadoria do Teable** (19/08/2026): export completo → R2, tabelas vivas → D1, containers congelados. Ver `17_UNIFICACAO_DE_DADOS.md` |

**DoD:** VPS enxuta rodando 7 dias sem sentir falta de nada; backups testados (restore de amostra).

## Fase 3 — Primeiro template (piloto do Meta-SOP)

Construir o primeiro template de negócio seguindo as 6 etapas do `02_OPERATING_MODEL.md` §6 — este piloto valida a fábrica inteira.

**✅ ESCOLHIDO (18/07/2026): Canal dark**, começando por colocar o canal Spurgeon (`yt_en_treasures_spurgeon`) no ar. Os demais ficam pra Fase 5:

| Candidato | Ponto de partida | Prontidão |
|---|---|---|
| **Canal dark** ✅ | Esteira Spurgeon (narrate→transcribe→render+marketing) generalizada + RunPods + publicação | ~70% |
| Funil D2C (brand-in-a-box) | Bluue (Astro + quiz + tracking + domain_config) | ~60%, mas colide com a frente Bluue ativa |
| Site + membros | mananciapp | ~40% |

**Gaps reais mapeados na auditoria de 18/07 (o que falta pro Spurgeon ir ao ar):**
1. **Runtime preso no desktop do Gabriel** — `getPythonPath()` hardcoded em `C:\Users\Monegatto\...`; as tasks só executam com `trigger.dev dev` rodando no Windows local (PC desligado = fábrica parada). Decidir: deploy no trigger.dev cloud (build com python/ffmpeg) vs worker na VPS vs RunPods. (Nota: Kokoro TTS já roda na VPS dentro do `factorio_agents`.)
2. **Elo render pausado** — o encadeamento transcribe→render está comentado no `transcriber.ts` (só registra a task, não dispara).
3. **Publicação não existe** — a esteira termina no vídeo renderizado; falta `publish-to-youtube` (upload + título/descrição/tags + agendamento) e thumbnail.
4. **Fila via SQL bruto** — `get_pending_tasks.py` & cia falam psycopg2 direto no Postgres (funciona, mas depende do conserto da `tasks` — item 1.6 da Fase 1 — pra fábrica ter UI/API sãs).

**Plano "vídeo 100% no RunPods" (auditoria Remotion 18/07):** renderizador canônico = **Remotion `Sermon-Full-Production`** (validado ponta a ponta no sermão 0021 pelo Gabriel; `ffmpeg_renderer.py` vira fallback). Dockerfile + `rp_handler.py` (RunPods serverless → render → upload R2 `mananciall`) JÁ EXISTEM. Falta, nesta ordem:
1. **Consolidar assets no R2** — `public/storage/**` (sermon wavs, hooks/CTAs por sermão, library fixa: worship BGMs, intro/outro_cta_fixed) NÃO está no repo (localizar no PC/VPS e subir pro R2 com prefixo `channels/spurgeon/`). Visuais: só 2 catedrais + 1 busto em `remotion/public/images`.
2. **QR Code real + Worker de redirect (funil)** — `sample_qr.png` é placeholder (o QR quebrado do teste). Fix arquitetural: **domínio cravado `mananciall.org/en/treasures-spurgeon`** (canal é EN → app Mananciall precisa de i18n funcional antes do funil rodar). QR não aponta pro destino final: aponta pro **Worker de redirect** que loga o scan (D1) e repassa com UTMs.
   - **Regra do funil (definida 18/07):** o **QR fica SÓ no vídeo longo do YouTube** (viewer na TV/desktop escaneia com o celular). **Insta/TikTok são cortes com link clicável** (bio/descrição), sem QR — a pessoa já está no celular. Logo o QR é sempre `utm_source=youtube&utm_medium=qr`, variando só `v=<sermão>`. Um QR por vídeo, sem variante de plataforma.
   - **Formato do link:** `mananciall.org/go?s=yt&v=0001` → Worker → `/en/treasures-spurgeon?utm_source=youtube&utm_medium=qr&utm_campaign=spurgeon&utm_content=0001`. O mesmo Worker atende os cortes (`s=ig`/`s=tt`, link clicável). Destino editável pra sempre sem re-renderizar vídeo.
   - **A esteira do vídeo longo (atual) só precisa do QR do YouTube.** Cortes = esteira separada depois (reaproveita render + passo de clipagem).
3. **Assets remotos nos componentes** — templates usam `staticFile()` (só resolve `public/` local); criar helper `resolveAsset()` (http → src direto; senão staticFile) pros props aceitarem URLs do R2 no RunPods.
4. **Gerador de props** — `build_props` automático (props_21.json foi montado à mão): lê banco/R2 e cospe o JSON do sermão N.
5. **Deploy RunPods** — build da imagem, endpoint serverless, secrets R2, teste A/B com o sermão 0021 (comparar com o render local conhecido) + 2 sermões novos = os 3 de validação.
6. Depois dos 3 validados: página de destino do QR + Stripe (fase seguinte, já desacoplada pelo redirect).

**DoD:** 1 unidade nova lançada ponta a ponta pela skill `/novo-X` + 3 produções consecutivas limpas + template documentado no catálogo.

## Fase 4 — Departamentos por cadência

Ativar as rotinas das áreas (Operating Model §9): intel semanal, revisão de esteiras, calendário editorial. Definir a interface fábrica ↔ frente Br4nds (CRO diário consome dados do D1/Meta API sem editar o escopo da outra frente).

**DoD:** 2 semanas de rotinas estáveis com briefings que Gabriel considera úteis (não ruído).

## Fase 5 — Escala

- Template 2 e 3 (os candidatos restantes da Fase 3).
- Réplica do primeiro template em série (canal 2, 3, 4... com gate de qualidade por unidade).
- KPIs da fábrica no Teable: time-to-launch por unidade, custo por asset, receita por negócio, taxa de unidades limpas sem retrabalho.

**DoD:** segunda unidade do mesmo template lançada em < 1 dia de trabalho de sessão; KPIs visíveis no dashboard TASKS.

---

## ✅ Martelos batidos (18/07/2026)

| # | Decisão | Resultado |
|---|---|---|
| M1 | Arquitetura de dados | ✅ **Caminho C confirmado** (Outline narrativa + Teable tabular + git código) |
| M2 | Primeiro template da Fase 3 | ✅ **Canal dark** — prioridade máxima é o canal Spurgeon no ar |
| M3 | Timing do freeze do legado | ✅ **Aprovado matar tudo que não serve** — executar na ordem segura (destilar → exportar memórias → congelar reversível), sem atrapalhar o lançamento do canal |
