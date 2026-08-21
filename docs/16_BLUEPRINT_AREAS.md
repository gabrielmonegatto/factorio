# 🏭 BLUEPRINT DAS ÁREAS — Fábrica Eternall, piloto Mananciall

> Escrito em 19/08/2026 (sessão arquiteto com o Gabriel). Este doc é a FONTE do desenho
> das áreas; o Notion (página 🏭 Fábrica no Business System) é a vitrine gerenciável.
> Substitui a taxonomia do `02_OPERATING_MODEL.md` §8.
> Regra de atualização: mudou o desenho de uma área, atualiza AQUI e roda o builder
> (`tools/notion/notion-fabrica.mjs`) ou edita o Notion junto. Divergência entre os dois = bug.

**Decisões do Gabriel (19/08/2026):**
1. Sem pressa de receita: o que manda é TODAS as áreas em pé, ligando uma por uma,
   produzindo gradativamente mais com consistência.
2. Escopo: fábrica toda; Mananciall é o piloto (Bluue/ZOAC herdam o molde).
3. Notion é modelo/vitrine; um dia vira sistema próprio (estilo bi.br4nds.com.br).
   Logo: dado NUNCA mora só no Notion (ver §2).
4. 7 frentes (chats) abertas em paralelo, cada uma com prompt de abertura pronto (§6).

---

## §1 Taxonomia: as 7 áreas (+1 futura)

| # | Área | Missão em uma linha | Frente (onde o chat abre) |
|---|---|---|---|
| 1 | **Organização** | Toda sessão se orienta sozinha; aprendizado vira arquivo; nada se perde | `_factorio/` |
| 2 | **Inteligência de Mercado** | Saber quem vende o quê, como e por quanto; decisão ancorada em referência real | `_factorio/` |
| 3 | **Inteligência do Negócio** | Todos os números num painel confiável; fim do "no escuro" | `_factorio/` → repo `mananciall-bi` |
| 4 | **Mineração** | Matéria-prima (texto DP, dados, referências) entrando no banco em volume, com legalidade provada | `_factorio/scripts/mining/` |
| 5 | **Content** | Publicação diária consistente em todos os formatos a custo marginal ~zero | `_factorio/` (remotion/trigger) |
| 6 | **Productz** | Loja + biblioteca + app dignos de assinatura; do texto pronto ao vendável sem fricção | `apps/eternall/mananciall-site` |
| 7 | **i18n** | Cada ativo existe em EN/PT (depois ES) sem trabalho manual por idioma | `apps/eternall/mananciall-site` |
| 8 | Growth (FUTURA) | Tráfego pago, CRO, parcerias. Liga quando checkout+BI+conteúdo estiverem estáveis | (não abre chat ainda) |

Sub-frentes de Content (nomes do Gabriel, mantidos): **longz** (vídeos longos YouTube)
e **shortz** (Shorts/TikTok/Reels). Growth veio do esboço dele e fica registrada como futura.

**Estados de ativação de uma área** (campo Status no banco Áreas):
`Futura → Desenhada → Ligando (chat aberto, W0 em execução) → Rodando (W0 entregue,
produz ponta a ponta mesmo manual) → Consistente (14 dias sem furo nem socorro)`.

**Ordem de ativação** (meta: uma vira "Rodando" por vez, sem parar as outras):
1 Organização · 2 Content · 3 Mineração · 4 Productz · 5 Int. do Negócio · 6 Int. de Mercado · 7 i18n · 8 Growth.

---

## §2 Residência de dados (a decisão que o Gabriel pediu)

Regra-mãe (já validada na Biblioteca Mananciall e no BI Br4nds):
**máquina escreve na máquina; Notion é plano de controle humano + vitrine; sync de mão
única máquina→Notion, exceto campos onde o Gabriel manda** (prioridade, estado editorial,
lançamento). O sistema próprio futuro (estilo bi.br4nds.com.br) **lê da máquina, nunca do
Notion**: por isso o Notion é descartável por design e a migração futura é trocar a vitrine,
não mover dado.

| Dado | Casa canônica | Vitrine humana |
|---|---|---|
| Plano de catálogo (o que publicar, prioridade) | Notion `Biblioteca Mananciall` (controle humano) | ela mesma |
| Texto bruto minerado | D1 `mananciall-mining` | coluna Estado na Biblioteca |
| Produto (livros, capítulos, orders, entitlements) | D1 `mananciall-db` | `sync-notion.mjs` |
| Fatos de BI (métricas de canais/loja/esteiras) | D1 `mananciall-db`, tabela `bi_snapshots` ✅ 19/08 | banco `Indicadores` no Notion → depois app BI |
| Intel de mercado (canais, vídeos, players, criativos) | **D1 `eternall-intel`** ✅ 19/08 | curadoria em `Referências de Editoras`; síntese em página |
| Estado de esteiras (filas, pipeline) | D1 (por esteira; padrão `works`/`runs`) | banco `Esteiras` no Notion (status de alto nível) |
| Gestão da fábrica (áreas, roadmap, tarefas humanas) | Notion (`Áreas`, `Roadmap`, `Tasks`) | ele mesmo; grão fino de esteira NUNCA vira task |
| Código, SOPs (skills), docs, templates | git (`_factorio/`, repos dos apps) | catálogo de 1 linha |
| Binários (áudio, vídeo, capas, snapshots crus) | R2 (`mananciall`, `channels`, `eternall-archives`) | páginas apontam URL |
| Credenciais | `_factorio/.env` | NUNCA em lugar nenhum |

> **Atualização de 19/08 (noite):** o Teable foi aposentado e o trigger.dev saiu da stack.
> Todo o dado de máquina agora mora no D1. Detalhe completo em `17_UNIFICACAO_DE_DADOS.md`.

---

## §3 Mapa do Notion (montado em 19/08/2026)

Tudo sob a página **Business System** (`33d6bf27-9f65-4043-8a5d-c53fe0b241a3`).
Página-hub: **🏭 Fábrica** (id no `tools/notion/notion-fabrica-ids.json`).

| Banco | O que é | Origem |
|---|---|---|
| `Áreas` | As 8 linhas de cima + sub-frentes; blueprint completo na página de cada linha | é o ex-"Mananciall Roadmap" do Gabriel, upgradado in place (nada apagado) |
| `Roadmap` | Entregas/marcos por área e onda (W0/W1/W2), com gate e status | novo |
| `Esteiras` | Inventário de automações/workflows: status, camada, código, cadência | novo |
| `Indicadores` | Catálogo de métricas por área (padrão do 📏 Catálogo de Métricas do Br4nds) | novo |
| `Tasks` | Banco existente (57 linhas); ganhou relation `Área`; tarefas de fábrica entram aqui | existente |
| `Biblioteca Mananciall` | Plano de controle do catálogo (202 obras) | existente |
| `Referências de Editoras` | Intel de mercado (609 produtos BR; W0 adiciona mercado EN) | existente |

Regras de escrita: máquina (scripts com `NOTION_TOKEN` de `_factorio/.env`, kit em
`tools/notion/`) escreve campos de máquina e cria tasks; Gabriel manda em prioridade,
status editorial e gates. Views (kanban, filtros) são manuais na UI: a API não cria view.

---

## §4 Ondas

Cada área tem 3 ondas internas. Definições:

- **W0 Ligar**: o mínimo pra área produzir o output dela ponta a ponta (mesmo com passo manual).
- **W1 Consistência**: cadência sem furo, alarme cobrindo, zero socorro não planejado.
- **W2 Escala**: mais volume/formatos/idiomas com o mesmo esforço humano.

Detalhe por área no §6. O quadro gerenciável vive no banco `Roadmap` do Notion.

---

## §5 Gates do Gabriel (consolidado, 19/08/2026)

Ações que SÓ ele pode fazer e que bloqueiam entregas. Cada uma existe como task
(Responsável Monegatto, prefixo GATE) no Notion:

> **Auditado por API em 19/08 (noite):** 5 destes gates já estavam resolvidos, o roadmap
> é que estava velho. Ficam registrados como ✅ pra ninguém "destravar" de novo.

| Gate | Área que destrava | Origem |
|---|---|---|
| ✅ I1: re-auth YouTube no canal Charles Spurgeon Treasures | Content | resolvido (canal publicando) |
| I2: decidir destino dos 5 vídeos públicos no canal pessoal | Content | `11_ROADMAP_ATIVO.md` |
| ✅ P0.4: autorizar run real do `schedule_channel.py` (1/dia) | Content | resolvido (1/dia desde 13/08) |
| ✅ Aprovar piloto de 5 shorts | Content | resolvido (1º Short no ar em 18/08) |
| ✅ Apagar CNAME `www` da Vercel | Productz | resolvido (www.mananciall.org responde 200) |
| **Criar webhook do Discord #fabrica** e colar em `DISCORD_WEBHOOK_FABRICA` | Organização | health check pronto, esperando só isso |
| Corrigir linha malformada no `.env` (`PADDLE_WEBHOOK_SECRET:` com `:`) | Organização | achado em 19/08 |
| Revogar token do Teable e chave `factorio_secret` ao desligar | Organização | estavam em texto plano no `STACK.md` commitado |
| F4.2: gates do canal de shorts (canal novo vs Spurgeon, cadência) | Content | idem |
| F4.3: criar apps/credenciais TikTok + Meta (review demora semanas) | Content (W2) | idem |
| Paddle: Website Approval (Checkout → Website Approval) | Productz | memória manancial-2-0 |
| Asaas: cadastrar conta bancária + enviar documentos | Productz | idem |
| Apagar CNAME `www.mananciall.org` da Vercel (aí anexo o www) | Productz | idem |
| Aprovar golden set da wiki (5 verbetes GOLDEN_REVIEW) | Content (wiki) | memória mananciall-wiki |
| F2.4: decidir voz PT/ES (locutor contratado ~$50-200 com cláusula) | i18n | `11_ROADMAP_ATIVO.md` |
| F3.1: conferir billing do Lightning Studio | Content (infra) | idem |
| Decisão: assinatura mensal R$12 da Bíblia Jornada (1 assinante) | Productz | memória manancial-2-0 |

---

## §6 As áreas

### 6.1 Organização

**Missão**: toda sessão se orienta sozinha em minutos; aprendizado vira arquivo na hora;
alarme cobre o que roda sozinho. **Norte 90d**: 7 frentes rodando sem colisão, docs
confiáveis, esteiras com health check.

**Já existe**: docs 00 a 16, constituição (`_factorio/CLAUDE.md`), skills `/fabrica`,
`/nova-skill`, `/handoff-frente`, kit Notion (30 scripts), `backlog_skills_seed.md`.

**W0 Ligar**: (a) este blueprint no git + Notion montado ✅ 19/08; (b) webhook Discord
#fabrica + health check: esteira com erro OU 48h sem vídeo novo agendado → aviso (item
P0.5, deixou de ser opcional); (c) skill `/frente` que abre sessão de área lendo doc 16 +
Notion; (d) índice e OM atualizados pra taxonomia nova ✅ 19/08.
**W1**: `/diretor-diario` manual 3x (lê D1/Teable/Notion → briefing de 10 linhas);
conserto da tabela `tasks` do Teable (item 1.6 do `04_ROADMAP.md`); backup git (push
remoto dos repos que ainda não têm). **W2**: cadências agendadas (diretor diário
automático, revisão de esteiras semanal), promoção de skills 🟡→🟠→🟢.

**Dados**: docs/skills em git; tasks humanas no Notion; estado de esteira em Teable/D1.
**Indicadores**: skills por nível de confiança; frentes com handoff limpo; incidentes de
colisão de frente (meta 0). **Gates**: nenhum.
**Território**: `_factorio/docs/`, `_factorio/.claude/skills/`, `_factorio/tools/notion/`, `_factorio/scripts/org/`.

### 6.2 Inteligência de Mercado

**Missão**: mapa vivo de quem vende o quê no nosso espaço (livraria cristã digital, app
de Bíblia, canais dark de sermão), com síntese que muda decisão de catálogo, preço, capa
e copy. **Norte 90d**: mercado EN mapeado no mesmo nível que o BR + rotina semanal.

**Já existe**: banco `Referências de Editoras` (609 produtos: Heziom + Biblioteca
Católica, com sistema de capas decodificado), dossiês no repo do site
(`docs/DOSSIE-FRONTEND-2026.md`, `REFERENCIAS-CONVERSAO.md`, `docs/capas/`),
docs 13/14 (catálogo estratégico), benchmark GotQuestions (wiki).

**🎁 Acervo resgatado em 19/08 (mude o plano por causa disto):** o Teable guardava, abandonado
desde abril, um mapeamento que agora vive no D1 `eternall-intel`: **50 canais concorrentes**
com inscritos/views, **36.739 vídeos** com views, engajamento e categoria (raio-X do que
performa no nicho), **17 players**, **1.421 anúncios com copy** e **293 páginas de concorrente
raspadas**. A W0 deixou de ser "mapear do zero".

**W0 Ligar**: (a) **explorar e sintetizar o que já temos** (o que performa nos 36 mil vídeos:
formato, duração, tema, título) e transformar em regra editorial pros nossos canais;
(b) **reativar a coleta** (YouTube API → `channels`/`channel_videos`, parada desde abril);
(c) fechar os dois gaps reais, que são **players EN** (Standard Ebooks, Monergism, Banner of
Truth, Crossway, Ligonier) e o **segmento de apps** (YouVersion, Logos, Olive Tree);
(d) síntese "Mapa do Mercado" (1 página por segmento) na página da área.
Os três segmentos: **livraria** (disputa o mesmo dinheiro do mananciall.org), **app** (disputa
com o Mananciall Bible), **canais** (disputa a mesma atenção dos nossos canais). **W1**: rotina `/intel-semanal` (novidades, preços, lançamentos, formatos; 3
edições seguidas úteis); monitor de canais concorrentes por YouTube API (números →
Teable). **W2**: data lake no Teable (regra: estruturado→Teable, síntese→Notion),
alertas de movimento (player novo, preço mudou).

**Dados**: curadoria no Notion; scrape/volume no Teable; binários (prints, capas) no R2.
**Indicadores**: players mapeados EN vs BR; relatórios de intel entregues; decisões
citando intel (qualitativo). **Gates**: nenhum.
**Território**: `_factorio/scripts/intel/` (criar), páginas/bancos de intel no Notion.

### 6.3 Inteligência do Negócio

**Missão**: todos os números relevantes (canais, loja, esteiras, custos) num painel
diário confiável; nenhuma decisão no escuro. **Norte 90d**: BI Mananciall no ar no padrão
do bi.br4nds.com.br, com alarmes ligados no #fabrica.

**Já existe**: padrão pronto do Br4nds (repo React+Functions+D1 + rebuild noturno na VPS
+ 📏 Catálogo de Métricas com 38 métricas + vigia de banco no rodapé); dados espalhados:
YouTube Studio, D1 `mananciall-db` (leads/orders/entitlements), Paddle, Asaas, R2, D1
`mananciall-mining`.

**W0 Ligar**: (a) catálogo de indicadores Mananciall no banco `Indicadores` (núcleo de
~20, semeado 19/08: validar/editar); (b) script `snapshot.mjs`: coleta YouTube API + D1
produção + D1 mineração + Paddle/Asaas → grava em `bi_snapshots` (D1) → espelha valor
atual no Notion. Rodar 1x/semana manual. **W1 ✅ ENTREGUE 19/08 (noite)**: repo
`apps/eternall/mananciall-bi` NO AR em **bi.mananciall.org** (Worker + React, tema
Vercel do padrão Br4nds). Mudou de forma com decisão do Gabriel: em vez de abas de
gráfico, nasceu como **tabelas estilo Notion dirigidas por registro**
(`shared/tabelas.js`): views salvas, filtro com contagem, board com arrastar, edição
inline auditada (`bi_edicoes`) nos campos de curadoria. 7 telas: Biblioteca (202 obras
semeadas do Notion e EDITÁVEL: é o novo plano de controle), Loja, Fila de mineração,
Indicadores, Canais, Vídeos do nicho, Anúncios. Senha = a do superadmin do site.
Transição registrada como tasks: mineração reponta `queue.mjs` pro D1; site escreve
campos de máquina no D1; gate do Gabriel = validar 2 semanas e aposentar a Biblioteca
do Notion. **W2**: gráficos de leitura sobre `bi_snapshots`; alarmes de negócio (venda
zerada, publicação parada → #fabrica, junto com o health check da Organização);
atribuição do funil `/go` (scan → visita → venda).

**Dados**: fatos em D1 (`bi_snapshots`); Notion `Indicadores` é vitrine; app BI lê do D1.
**Indicadores**: freshness do snapshot (dias); % métricas com coleta automática.
**Gates**: nenhum (tokens existem no `.env`).
**Território**: `_factorio/scripts/bi/` (criar); na W1, repo novo `apps/eternall/mananciall-bi` ("tocou, versiona": `git init`).

### 6.4 Mineração

**Missão**: qualquer obra do mapa vira texto bruto no banco em horas, com proveniência e
domínio público provados; e a matéria-prima não para em livro (sermões, hinos, cartas,
gravuras, perguntas). **Norte 90d**: fila nunca vazia, 149 sem-URL zerados, ponte pra
produção rodando.

**Já existe**: esteira completa (`scripts/mining/`: queue/resolve/mine/status, doc 15),
24 obras / 231 caps / 14M chars minerados, 3 travas (similaridade pelo maior conjunto,
autor concordando, trava de copyright que já pegou a Outler 1955), `content_index` com
545 obras, fetch educado. Limpeza/edição NÃO é daqui (é esteira do repo do site, já
rodou em 3.342 caps).

**W0 Ligar** (nesta ordem): (a) **ponte minerado→produção**: promover obra `mined` pra
`books` + `chapters.source_md` na produção com gate de conferência (é a peça que falta
pro fluxo inteiro girar); (b) atacar o gargalo resolver: adapter **Archive.org** (21
obras esperam) + ampliar `content_index` com mais fontes até zerar os 149 sem URL;
(c) snapshot cru → R2 (`raw_key`, prova de proveniência, evita re-raspar).
**W1**: corte de capítulo do New Advent; obras compostas (volumes editoriais montados
peça a peça); cron de mineração (fila sempre andando sozinha). **W2**: minerar além de
livro: sermões avulsos (51 volumes Spurgeon), comentários bíblicos pro app, perguntas
FAQ (benchmark GotQuestions), gravuras DP pra capas.

**Dados**: fila/estado/texto em D1 `mananciall-mining`; plano na Biblioteca (Notion);
cru no R2. **Indicadores**: obras mineradas/semana; % da fila sem URL; bloqueadas por
DP; capítulos promovidos pra produção. **Gates**: nenhum.
**Território**: `_factorio/scripts/mining/`, `docs/15_ESTEIRA_DE_MINERACAO.md`.
A ponte escreve no D1 de produção: coordenar formato com a frente Productz via handoff.

### 6.5 Content

**Missão**: publicar todo dia, em todos os formatos, com qualidade estável e custo
marginal ~zero. Sub-frentes: **longz** (YouTube longos), **shortz** (Shorts/TikTok/
Reels), wiki/artigos. **Norte 90d**: 1 longo/dia + shorts diários sem furo, canal Bíblia
no ar, wiki com cluster Oração público.

**Já existe**: 113 sermões renderizados (só 6 no canal certo; resto travado nos gates),
pipeline híbrido validado (~$0,10/vídeo), guardião de canal, fábrica de shorts F4.4
(piloto de 5 no R2), canal Bíblia desenhado (doc 10; KJV + am_michael escolhidos),
copy visceral dos 113, wiki F0 (manual + 5 verbetes golden), 731 leituras diárias no
banco, 112 sermões narrados (~4 meses de acervo).

**W0 Ligar** (é DESTRAVAR, não construir): gates I1 + P0.4 + piloto shorts (§5) →
com I1 feito: limpar estado do R2 dos 18 vídeos do canal errado (I3), reativar cron
(I4), F4.5 fila de shorts automática. Resultado: publicação diária no automático.
**W1**: canal Bíblia no ar (F1.4 a F1.7: A/B Kokoro vs Chirp, blocos ~1h, camada visual
anti "conteúdo reutilizado", canal+OAuth novo JÁ com app em produção); wiki F1/F2
(schema D1 + rotas reais + cluster Oração público). **W2**: cortes TikTok/Meta (gate
F4.3), blog SEO por clusters, carrossel/imagem (esteira nova), canais PT/ES (depende
i18n voz), 2º canal dark pelo template.

**Dados**: assets e renders no R2; estado do agendador em JSON no R2 (migrar pra Teable
na W1); wiki editorial no Teable `wiki_articles`; métricas → BI.
**Indicadores**: longos publicados/semana (meta 7); shorts/semana; dias sem furo;
subs/views; scans do QR `/go`. **Gates**: I1, I2, P0.4, piloto shorts, F4.2, F4.3,
golden set wiki, F3.1.
**Território**: `_factorio/remotion/`, `_factorio/trigger/`, `_factorio/scripts/` (canais), docs 06/07/10/11/12. Wiki editorial: coordenar com Productz (rotas no repo do site) via handoff.

### 6.6 Productz

**Missão**: catálogo digno de assinatura: loja + leitor + audiolivro + app de estudo;
do "Texto pronto" ao vendável sem fricção. **Norte 90d**: checkout live nas 2 moedas,
50+ obras publicadas com capa v1, /today no ar, membros v1.

**Já existe**: mananciall.org no ar (EN + PT completos, 27 livros, leitor com amostra
pública cap. 1, superadmin, acervo privado Banzoli 1.114 caps), Paddle integrado
(26 produtos, cupom teste) e Asaas integrado (Pix), ambos travados em aprovação de
conta; 9 audiolivros completos (1.214 faixas); esteira de edição (portão letra a letra);
frente de capas aberta (spec v0.2 + 609 referências + gramática Biblioteca Católica
decodificada); app Bíblia fases 0/1 no ar; Bíblia Jornada legada (31 dias, 10 assinantes
Stripe, anuais em cancel_at_period_end).

**W0 Ligar**: (a) checkout live: gates Paddle/Asaas/www (§5) + 1 venda de teste ponta a
ponta em cada moeda (cupom 100% + Pix R$1); (b) rota **`/go`** + log de scan em D1
(os vídeos publicados JÁ carregam QR pra `mananciall.org/go?s=yt&v=NNNN`: hoje é 404,
é a ponte vídeo→loja); (c) **capas v1**: renderer programático por coleção (caminho
barato validado: retrato duotone estilo Tratados Puritanos + 1 cor por coleção) nos 27
live; (d) **/today** no ar (731 leituras Morning and Evening prontas no banco: SEO +
destino diário dos canais). **W1**: lote de publicação (obra promovida pela mineração →
edição → live na loja, meta +20 obras); audiolivros novos (esteira TTS com a voz EN
atual); membros v1 (Clerk no lugar do cookie PREVIEW) + migração Bíblia Jornada
(vitalício no site novo). **W2**: app Bíblia fases 2 a 4 (Strong's, referências
cruzadas, comentários: casa com a mineração W2), coleções/bundles, assinatura estilo
clube (modelo Biblioteca Católica), blog /today expandido.

**Dados**: produto no D1 `mananciall-db`; plano na Biblioteca (Notion); capas/áudio no
R2; vendas nos gateways espelhadas em `orders`. **Indicadores**: livros live; vendas e
receita/semana; leads; % catálogo com capa v1; conversão PDP (quando BI medir).
**Gates**: Paddle approval, Asaas docs, www CNAME, decisão mensal Jornada, preços
(campo dele na Biblioteca). **Território**: repo `apps/eternall/mananciall-site`
(e `mananciallbible` quando a frente do app reabrir). Não toca `_factorio` além de ler.

### 6.7 i18n

**Missão**: cada ativo (livro, página, verbete, vídeo) existe em EN e PT (ES na fila)
sem retrabalho manual. **Norte 90d**: esteira de tradução EN→PT validada em livros
vendáveis + decisão de voz PT tomada.

**Já existe**: site bilíngue com hreflang e rotas PT traduzidas; 2 livros PT vendáveis +
26 "em breve"; 4 Bíblias PT em JSON; decisão EN-first (24/07); pesquisa de voz PT/ES
(F2: Kokoro reprovado, recomendação F2.4 = locutor contratado); wiki desenhada PT
mestre → EN gêmeo.

**W0 Ligar**: esteira de tradução de livro EN→PT como LLM-função com portão de
qualidade no molde da edição (não muda sentido; glossário teológico consistente;
amostragem por juiz; grafia de época opt-in) + piloto: 1 livro curto do catálogo
(candidato: All of Grace) publicado vendável em `/pt`. **W1**: rotina: todo livro novo
publicado EN entra na fila PT; traduzir verbetes wiki (PT mestre → EN); voz PT (gate
F2.4) → piloto de audiolivro/canal PT. **W2**: ES (site + livros), canais PT/ES com a
voz definida, tradução de metadados/legendas em lote.

**Dados**: tradução vira `chapters` PT no D1 produção (mesma casa do livro EN);
glossário teológico em git (`_factorio/docs/` ou repo do site); fila em D1.
**Indicadores**: livros PT vendáveis; verbetes EN; % catálogo bilíngue.
**Gates**: F2.4 (voz), preço BRL (dele). **Território**: repo
`apps/eternall/mananciall-site` (esteira de tradução vive lá, perto da edição);
coordenar com Productz (mesmo repo!): i18n só toca `scripts/i18n/` + conteúdo PT,
e ambas as frentes commitam pequeno e cedo pra não conflitar.

### 6.8 Growth (futura)

Tráfego pago, CRO (Experimentos/ICE já existem no Notion), SEO técnico, parcerias,
e-mail (The Machine é o precedente Bluue). **Critério de ativação**: checkout live +
BI medindo + 30 dias de publicação consistente. Até lá, growth orgânico é papel do
Content (canais) e do Productz (SEO /today, amostras públicas).

---

## §7 Regras das 7 frentes em paralelo

1. **1 chat = 1 área = 1 território de arquivos** (definido em cada área acima).
   Precisou mexer fora: `/handoff-frente`, nunca "eu aproveito e mexo".
2. **Productz e i18n dividem o repo do site**: commits pequenos, `git pull` no início
   da sessão, i18n restrita a `scripts/i18n/` + conteúdo PT.
3. **Toda sessão termina com**: commit no repo da frente + tasks atualizadas no Notion
   (kit `tools/notion/`) + report de 10 linhas. *(Decisão de 20/08: gestão humana =
   Notion, 1000 a 0 na preferência do Gabriel; tarefa é MACRO, micro vira checklist
   dentro da página. O BI/D1 cuida de dado e curadoria de catálogo. A ida-e-volta
   tarefas→D1→Notion do dia 20 fica de lição: a regra "humano cura → Notion" já
   estava certa desde o início.)*
4. **Gate é do Gabriel**: frente bloqueada por gate não contorna; cobra o gate no
   report e segue pra próxima entrega da fila.
5. **Aprendizado vira arquivo na hora** (skill/doc do território da frente), senão morreu.
6. Estado fino de esteira NUNCA vira task no Notion (1 task = 1 operação de alto nível).

## §8 Prompts de abertura das 7 frentes

Prontos pra colar, um por chat. Também estão na página de cada área no Notion.

### Frente 1 · Organização

```
Você é a frente ORGANIZAÇÃO da fábrica Eternall (piloto Mananciall).
Abra em C:\Users\Monegatto\Desktop\EternalL\_factorio e rode /fabrica.
Leia: docs/16_BLUEPRINT_AREAS.md (§6.1 e §7) e docs/04_ROADMAP.md (itens 1.3 e 1.6).
Missão W0, nesta ordem:
1. Webhook Discord #fabrica + health check das esteiras (erro OU 48h sem vídeo novo
   agendado → aviso). Item P0.5 do docs/11_ROADMAP_ATIVO.md.
2. Skill /frente: abre sessão de qualquer área carregando doc 16 + tasks do Notion.
3. Preparar /diretor-diario (skill draft; primeira execução manual é W1).
Tarefas: Notion, banco Tasks, filtro Área=Organização (kit tools/notion, NOTION_TOKEN no .env).
Território: docs/, .claude/skills/, tools/notion/, scripts/org/. Fora disso: /handoff-frente.
Fim de sessão: commit + Notion atualizado + report de 10 linhas.
```

### Frente 2 · Inteligência de Mercado

```
Você é a frente INTELIGÊNCIA DE MERCADO da fábrica Eternall (piloto Mananciall).
Abra em C:\Users\Monegatto\Desktop\EternalL\_factorio e rode /fabrica.
Leia: docs/16_BLUEPRINT_AREAS.md (§6.2 e §7), docs/13_CATALOGO_ESTRATEGICO_MANANCIALL.md
e, no repo do site (só leitura), docs/DOSSIE-FRONTEND-2026.md e docs/capas/HANDOFF-CAPAS.md.
Missão W0: mapear o mercado EN no banco "Referências de Editoras" do Notion (campo
Mercado=EN): Standard Ebooks, Monergism, Banner of Truth, Crossway, Ligonier,
YouVersion/Logos/Olive Tree (apps) e 10+ canais YouTube de sermão/audiobook EN.
Por player: catálogo, preço, formato, modelo (free/pago/assinatura), capa, o que copiar.
Entrega: síntese "Mapa do Mercado EN" na página da área Inteligência de Mercado no Notion.
Tarefas: banco Tasks, filtro Área=Inteligência de Mercado.
Território: _factorio/scripts/intel/ (criar) + Notion. Não edita repo de app.
Fim de sessão: commit + Notion atualizado + report de 10 linhas.
```

### Frente 3 · Inteligência do Negócio

```
Você é a frente INTELIGÊNCIA DO NEGÓCIO (BI) da fábrica Eternall (piloto Mananciall).
Abra em C:\Users\Monegatto\Desktop\EternalL\_factorio e rode /fabrica.
Leia: docs/16_BLUEPRINT_AREAS.md (§6.3 e §7). Padrão a seguir: memória br4nds-bi
(bi.br4nds.com.br) e o banco "📏 Catálogo de Métricas — BI" no Notion.
Missão W0:
1. Revisar o banco Indicadores no Notion (semeado 19/08) e propor ajustes ao Gabriel.
2. Construir _factorio/scripts/bi/snapshot.mjs: YouTube API + D1 mananciall-db +
   D1 mananciall-mining + Paddle/Asaas → tabela bi_snapshots (D1) → espelhar "Valor
   atual"/"Atualizado em" no banco Indicadores. Rodar e conferir números à mão.
3. Documentar a rodada semanal (por ora manual) na página da área.
W1 (não começar sem W0 verificado): repo apps/eternall/mananciall-bi no padrão Br4nds.
Tarefas: banco Tasks, filtro Área=Inteligência do Negócio.
Território: _factorio/scripts/bi/. Credenciais no .env (CRLF: tr -d '\r').
Fim de sessão: commit + Notion atualizado + report de 10 linhas.
```

### Frente 4 · Mineração

```
Você é a frente MINERAÇÃO da fábrica Eternall (piloto Mananciall).
Abra em C:\Users\Monegatto\Desktop\EternalL\_factorio e rode /fabrica.
Leia: docs/16_BLUEPRINT_AREAS.md (§6.4 e §7) e docs/15_ESTEIRA_DE_MINERACAO.md inteiro.
Estado: 24 obras mineradas; gargalo é resolver (149 sem URL); ponte pra produção não existe.
Missão W0, nesta ordem:
1. PONTE minerado→produção: promover obra mined do D1 mananciall-mining pra books +
   chapters.source_md do D1 mananciall-db (formato: conferir com a frente Productz via
   handoff; a esteira de edição de lá assume depois). Piloto com 1 obra, conferida.
2. Adapter Archive.org (21 obras esperam) + ampliar content_index até zerar os 149.
3. Snapshot cru no R2 (raw_key): prova de proveniência, evita re-raspar.
Respeite as 3 travas do doc 15 (similaridade, autor, copyright). Fontes com fetch educado.
Tarefas: banco Tasks, filtro Área=Mineração. O painel humano é a Biblioteca Mananciall.
Território: _factorio/scripts/mining/ + docs/15. Escrita no D1 de produção SÓ pela ponte.
Fim de sessão: commit + Notion atualizado + report de 10 linhas.
```

### Frente 5 · Content

```
Você é a frente CONTENT da fábrica Eternall (sub-frentes longz e shortz).
Abra em C:\Users\Monegatto\Desktop\EternalL\_factorio e rode /fabrica.
Leia: docs/16_BLUEPRINT_AREAS.md (§6.5 e §7), docs/11_ROADMAP_ATIVO.md (incidente I1 +
P0), docs/12_FABRICA_SHORTS.md e docs/10_CHECKLIST_CANAL_BIBLIA.md.
Estado: 113 longos renderizados e 112 narrados; publicação parada nos gates I1/P0.4;
piloto de 5 shorts no R2 aguardando aprovação.
Missão W0 (é destravar, não construir):
1. Preparar tudo que NÃO depende de gate: F4.5 (fila de publicação de shorts), I3
   (limpeza do estado do R2 dos 18 vídeos do canal errado) pronto pra rodar pós-I1.
2. Assim que o Gabriel fizer I1/P0.4/aprovar shorts: executar I3, reativar cron (I4),
   ligar fila de shorts. Meta: 1 longo/dia + shorts diários no automático.
3. Com publicação girando: iniciar W1 = canal Bíblia (F1.4 a F1.7 do doc 10; OAuth novo
   JÁ com app em produção, lição do I1: token tem que provar IDENTIDADE de canal).
Gates seus (cobrar no report, nunca contornar): I1, I2, P0.4, piloto shorts, F4.2, F4.3.
Tarefas: banco Tasks, filtro Área=Content.
Território: remotion/, trigger/, scripts/ (canais), docs 06/07/10/11/12.
Fim de sessão: commit + Notion atualizado + report de 10 linhas.
```

### Frente 6 · Productz

```
Você é a frente PRODUCTZ da fábrica Eternall (Mananciall).
Abra em C:\Users\Monegatto\Desktop\EternalL\apps\eternall\mananciall-site (repo próprio;
git pull antes: a frente i18n divide este repo).
Leia: CLAUDE.md do repo, docs/ACERVO.md, docs/capas/HANDOFF-CAPAS.md e, na fábrica (só
leitura), _factorio/docs/16_BLUEPRINT_AREAS.md (§6.6 e §7).
Estado: site EN+PT no ar em mananciall.org; Paddle e Asaas integrados mas travados em
aprovação de conta (gates do Gabriel); 27 livros live; 9 audiolivros; QR dos vídeos
aponta pra /go que hoje é 404.
Missão W0, nesta ordem:
1. Rota /go (s=yt&v=NNNN): loga scan em D1 + redireciona com UTMs pro destino
   (/en/treasures-spurgeon quando existir; por ora home EN com UTM). Desbloqueia o funil
   dos vídeos JÁ publicados.
2. Página /today: leitura diária do Morning and Evening (731 prontas no banco),
   indexável, CTA pro livro. Destino diário dos canais + SEO.
3. Capas v1: renderer programático por coleção (retrato duotone + 1 cor por coleção,
   caminho barato do HANDOFF-CAPAS) aplicado aos 27 live.
4. Quando os gates Paddle/Asaas/www saírem: 1 venda de teste ponta a ponta por moeda.
Gates seus: Paddle Website Approval, Asaas docs, CNAME www, decisão Jornada mensal.
Tarefas: banco Tasks, filtro Área=Productz. Preço/lançamento: Gabriel manda na
Biblioteca Mananciall.
Fim de sessão: commit + Notion atualizado + report de 10 linhas.
```

### Frente 7 · i18n

```
Você é a frente I18N da fábrica Eternall (Mananciall).
Abra em C:\Users\Monegatto\Desktop\EternalL\apps\eternall\mananciall-site (repo
compartilhado com a frente Productz: git pull antes, commits pequenos, seu território é
scripts/i18n/ + conteúdo PT).
Leia: CLAUDE.md do repo, src/lib/i18n.ts, a esteira de edição (scripts/editoria/) e, na
fábrica (só leitura), _factorio/docs/16_BLUEPRINT_AREAS.md (§6.7 e §7).
Missão W0: esteira de tradução de livro EN→PT como LLM-função com portão de qualidade
no molde da edição: não muda sentido (amostragem com juiz), glossário teológico
consistente (criar docs/GLOSSARIO-PT.md no repo), grafia de época opt-in por livro.
Piloto: All of Grace (curto, Spurgeon, já tem áudio EN) publicado vendável em /pt,
revisão por amostragem antes de ir live.
Depois do piloto aprovado: fila = próximos 5 livros curtos do catálogo.
Gate seu: voz PT (F2.4) é decisão do Gabriel; não iniciar audiolivro PT antes.
Tarefas: banco Tasks, filtro Área=i18n.
Fim de sessão: commit + Notion atualizado + report de 10 linhas.
```
