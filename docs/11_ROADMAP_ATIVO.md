# 🗺️ ROADMAP ATIVO — frentes em andamento

> Quadro vivo. **Atualizado: 21/08/2026** (F6 Moody aberta)
> Antes: **19/08/2026** (auditoria por API: o que estava escrito aqui
> não era mais verdade).
> Regra: item só sai daqui com verificação real (comando rodado, número medido).
> O quadro gerenciável por área vive no Notion (🏭 Fábrica); este doc é o detalhe técnico.

---

# ✅ RESOLVIDO — o canal está publicando (medido em 19/08/2026)

**A lição desta auditoria:** o roadmap escrito em 11/08 dizia "canal parado, gates
travados". A verificação por API mostrou o contrário. **Documento envelhece; número
medido não.** Por isso a skill `/frente` obriga a medir antes de planejar.

Estado real do canal `Charles Spurgeon Treasures` (`UCXqp7wuorli1uLZKJM96T6Q`):

| Fato | Valor |
|---|---|
| Token OAuth aponta pro canal | ✅ o certo (guardião confere identidade) |
| Vídeos publicados | 15 (4 inscritos, 91 views) |
| Cadência | 1 longo/dia às 12:00 desde 13/08 |
| Shorts | 1º publicado em 18/08 |

- [x] ✅ **I1** re-auth no canal certo — feito
- [x] ✅ **I4** cron religado — publicando
- [x] ✅ **P0.4** agendador autorizado — rodando
- [x] ✅ Piloto de shorts aprovado — 1 no ar
- [ ] **F4.5** falta a CADÊNCIA diária de shorts no automático (hoje é 1 avulso)
- [ ] **I2** decidir o destino dos 5 vídeos públicos no canal pessoal (gate do Gabriel)

🔴 **Urgência descoberta na auditoria:** os 15 vídeos publicados carregam QR pra
`mananciall.org/go`, que **devolve 404 hoje**. Cada vídeo no ar sem essa rota é
tráfego jogado fora. É a entrega nº 1 da frente Productz.

---

# 📕 HISTÓRICO — incidente 11/08 (resolvido, mantido pela lição)

A re-auth de 07/08 foi feita na **conta pessoal do Gabriel**, não no canal do
projeto. Nada deu erro: o token renovava, a API respondia 200, o agendador
reportava sucesso. E os vídeos subiam pro canal errado.

| Sermão | Canal onde foi parar |
|---|---|
| 0001 a 0006 | ✅ Charles Spurgeon Treasures (`UCXqp7wuorli1uLZKJM96T6Q`) |
| **0007 em diante** | ❌ **Gabriel Monegatto** (`UCdlZH_Y4pw9pyuQ5tWCWOFg`) |

Resultado: canal do projeto parado desde **03/08** (sermão 0006), e 5 vídeos do
projeto públicos no canal pessoal.

## Contenção (feita 11/08)

- [x] ✅ Cron do agendador **pausado** (`/etc/cron.d/factory`, backup `.bak_canal_errado`)
- [x] ✅ **13 vídeos privados desagendados** — iam virar públicos sozinhos no canal
      pessoal, 1/dia a partir de 12/08. Seguem privados, nada apagado.
- [x] ✅ **Guardião de canal** em `schedule_channel.py` e `publish_youtube.py`:
      toda obtenção de token confere `channels?mine=true` contra
      `EXPECTED_CHANNEL_ID` e **aborta** se não bater. Testado: bloqueia hoje.

## Conserto (pendente)

- [ ] **I1 — Gabriel:** rodar `auth_youtube.py` de novo e, na tela de escolha,
      selecionar **Charles Spurgeon Treasures**, não a conta pessoal.
      O guardião agora recusa qualquer outra, então não dá pra errar calado.
- [ ] **I2 — Gabriel (gate):** decidir o que fazer com os 5 públicos no canal
      pessoal (0007, 0009, 0010, 0011, 0014): apagar ou deixar privado?
- [ ] **I3** Depois do I1: limpar do estado do R2 os 18 vídeos do canal errado
      pra eles voltarem à fila e subirem no canal certo.
- [ ] **I4** Reativar o cron.

## Lição

**Token válido não prova canal certo.** Eu avisei o Gabriel pra escolher a conta
certa mas não verifiquei por API depois — sendo que a verificação é uma chamada.
Toda credencial nova agora tem que provar IDENTIDADE, não só validade.
Vale pro TikTok e pro Meta quando chegarem.

---

# 🔴 P0 — Spurgeon parou de publicar

**Diagnosticado em 04/08.** O canal está parado desde ~30/07 e ninguém foi avisado.

## O que está SÃO (verificado)

| Peça | Estado | Como conferi |
|---|---|---|
| Render 24/7 (`factory-producer.service`) | ✅ ativo há 3 dias | `systemctl is-active factory-producer` → `active` |
| Acervo renderizado | ✅ **113 de 113** | log: `prontos=113 \| fila vazia — dormindo` |
| Cron do agendador | ✅ rodou hoje 06:00 UTC | `/etc/cron.d/factory` + mtime do log |

Nada de infra quebrou. O produtor está dormindo porque **não sobrou trabalho**.

## O que está QUEBRADO (a causa raiz)

O `schedule_channel.py` morre ao renovar o token do YouTube:

```
error = invalid_grant
desc  = Token has been expired or revoked.
```

**Causa:** a tela de consentimento OAuth está em modo **"Testing"** no Google Cloud
Console. Nesse modo o Google **expira o refresh token em 7 dias**, sempre.
Linha do tempo: canal começou 29/07, agendou 6 vídeos, morreu em ~7 dias. Bate.

Só 6 vídeos entraram no calendário. Os outros 107 estão renderizados, prontos, parados.

## Conserto (nesta ordem)

- [x] ✅ **P0.2** App mudado de **Testing → In production** no Google Cloud Console.
      É este o conserto de raiz: o refresh token deixou de ter validade de 7 dias.
- [x] ✅ **P0.1** Re-auth feita. Token novo no `.env` local **e** no da VPS
      (backups em `.env.bak_pre_reauth` nos dois). Verificado: renova nos dois lados.
- [x] ✅ **P0.3** Scopes agora são `youtube.upload` + `youtube.force-ssl`
      (o segundo destrava postar comentário, que antes não dava).
- [x] ✅ **P0.6** Investigado o "buraco" do 0008: **ele não existe**. O prefixo dele
      no R2 está vazio, é falha na numeração do acervo, não render quebrado.
      Nada a consertar; a lista é montada do que existe no R2.
- [x] ✅ **P0.7** Cadência mudada pra **1 vídeo/dia permanente** (`UM_POR_DIA=True`).
      O modo 2/dia continua no código, é só desligar a flag.
- [x] ✅ **P0.8** Consertado o empilhamento: o rebase do calendário faz o primeiro
      não agendado cair amanhã e o resto seguir 1/dia. Dry-run limpo, sem colisão.
- [ ] **P0.4 — gate do Gabriel:** autorizar o run real do `schedule_channel.py`.
      Sobem 5 por run (`MAX_UPLOADS_PER_RUN`, folga na cota do YouTube); o cron
      diário das 06:00 UTC completa o resto sozinho.

## A lição que vale mais que o conserto

**A esteira não tem alarme.** Ela quebrou em 30/07 e só descobrimos em 04/08 porque
o Gabriel notou o canal parado. Seis dias de silêncio.

- [x] ✅ **P0.5 FEITO em 19/08**: `scripts/org/health_check.mjs` construído e verificado.
      Checa, numa rodada: canal publicou nas últimas 48h **e é o canal certo** (a lição
      do I1 virou código), bancos D1 respondendo, fila de mineração andando, site e
      catálogo vivos. Só grita quando há problema; manda 1 resumo verde por semana pra
      provar que o próprio alarme está vivo. **Falta só o Gabriel criar o webhook do
      Discord e colar em `DISCORD_WEBHOOK_FABRICA` no `.env`.**

---

# 🟡 F6 — D.L. Moody Treasures (2º canal da família, aberto 21/08/2026)

Canal: `Dwight Lyman Moody Treasures` (`UCX1HH8v0nQ03VLVq_DujdqA`), 0 vídeos.

| # | Item | Estado |
|---|---|---|
| F6.1 | Canal criado no YouTube + OAuth (`YT_MOODY_*`) | ✅ 21/08, token conferido pela API |
| F6.2 | Assets visuais: 5 bustos + 20 fundos + avatar + banner | ✅ bustos do Gemini, recortados |
| F6.3 | Acervo: 14 obras, 77 capítulos, 53h, mediana de 45min | ✅ minerado do Gutenberg |
| F6.4 | Funil `/go/moody` + biolink `/preacher/moody` | ✅ no ar, logando em `go_scans` |
| F6.5 | Watermark de inscrição | ✅ aplicado (HTTP 204) |
| F6.6 | Voz `am_adam` speed 0.84 | ✅ travada no A/B de 20/08 |
| F6.7 | **Narração dos 77 capítulos** | 🔴 **bloqueio real, ver abaixo** |
| F6.8 | 2 CTAs narrados (intro/outro) + 3 vídeos pré-renderizados | ⬜ |
| F6.9 | QR code do canal | ⬜ (gerado pelo build_job, falta rodar) |
| F6.10 | Coleção "The Best of D.L. Moody" na livraria (gate do Gabriel) | ⬜ |

## 🔴 F6.7 — o passo que ninguém tinha mapeado

Minerar coloca o TEXTO no D1. Entre o texto e o vídeo falta a etapa que
produz a pasta do sermão no R2 (`sermon_NN.wav` + `transcript.json` com
timing por palavra). Sem ela o `build_job` não tem o que baixar.

Quem fazia isso no Spurgeon é `scratch/workflows/spurgeon_generator/sermon_narrator.py`,
e ele está **órfão**: mora em `scratch/` (ignorado pelo git), lê de um
**Postgres local** que a fábrica aposentou quando migrou pro D1, e escreve num
caminho (`_factorio/toolbox/remotion/...`) que não existe mais. Ou seja: o
Spurgeon publica com um acervo já narrado no passado, e a etapa que o gerou
não roda mais.

**Custo real da decisão:** 53h de áudio. Na CPU da VPS o RTF medido é 10,6
(≈560h de processamento, inviável). Na RTX 3090 do RunPod o RTF é 0,34,
≈18h de GPU. **Gastar dinheiro é gate humano.**

## O que essa frente ensinou (vale pros outros 8 Treasures)

1. **Lote na fila de mineração é bug garantido.** Segunda vez que uma linha
   "obra A + obra B + obra C" fica `queued` pra sempre. Nenhum resolvedor acha
   URL pra três títulos grudados. Ver `expandir_moody.mjs`.
2. **Adotar a linha do lote, não pular.** A linha do lote carregava a URL da
   primeira obra; tratá-la como duplicata e depois bloqueá-la sumia com essa obra.
3. **"Resposta > 2000 chars" não prova download completo.** O Gutenberg derruba
   conexão sob carga e o pedaço passava por livro inteiro, virando capítulo
   picado no banco sem erro nenhum. Agora exige o marcador de fim do arquivo.
   *Isso também sabotou os testes: sem cache local, cada rodada dava um número
   diferente e eu estava calibrando extrator em cima de ruído.*
4. **Detector de capítulo precisa exigir SEQUÊNCIA.** "I., II., III." em ordem.
   Sem isso dispara em lista numerada dentro do sermão. E sequência que só
   começa depois de 40% do texto é a lista de anúncios da editora.
5. **Minerador nunca descarta texto.** Bloco curto gruda no vizinho.
6. **Nome de arquivo local é contrato com o `.tsx`.** O fundo do Moody vem de
   `hall/` e aterrissa como `cathedral_bg_cf_1.png` porque 8 templates chamam
   esse nome cravado.
7. **Um projeto do GCP pra fábrica inteira.** Projeto por canal é o que os
   Termos da API chamam de burlar cota, e a punição é suspender todos.
   Teto real: ~5 vídeos/dia somando os canais (hoje usamos 42% da cota).

---

# 🟡 F1 — Canal de narração bíblica (frente nova)

Checklist completo e minas em [`10_CHECKLIST_CANAL_BIBLIA.md`](10_CHECKLIST_CANAL_BIBLIA.md).

| # | Item | Estado |
|---|---|---|
| F1.1 | Tradução: **KJV primeiro**, WEB depois | ✅ 03/08 |
| F1.2 | Voz EN: **`am_michael`**, speed 0.80, pausa 0,75s | ✅ 03/08 |
| F1.3 | Regra de pausa (cortar em ponto, aparar pontas, emendar) | ✅ documentada |
| F1.4 | Motor: Kokoro (grátis, montado) vs Google Chirp 3 HD (grátis na cota, melhor) | ⬜ falta A/B |
| F1.5 | Formato dos blocos (~1h, ~100 a 120 vídeos) | ⬜ |
| F1.6 | Camada original (visual, trilha, edição) contra "conteúdo reutilizado" | ⬜ |
| F1.7 | Canal + OAuth + publicação | ⬜ |

**Escala:** 66 livros, 1.189 capítulos, ~783 mil palavras, **~93h de áudio**.
Roda de graça na CPU da VPS. Não precisa de GPU.

---

# 🟡 F2 — Voz nativa PT e ES (Spurgeon lateralizado)

**O problema:** clonar o `bm_george` (inglês) pra falar português preserva o timbre
mas arrasta a prosódia inglesa. Sai um gringo com português impecável, e o ouvido
pega na hora.

| # | Item | Estado |
|---|---|---|
| F2.1 | Kokoro PT/ES nativo | ❌ reprovado (vozes fracas) |
| F2.2 | OmniVoice modo design | ❌ reprovado (só 23 atributos objetivos, sem interpretação) |
| F2.3 | Clonagem de referência nativa (MLS + VoxPopuli) | 🔶 8 candidatos garimpados, clonagem interrompida |
| F2.4 | Locutor contratado com direito de clonagem por escrito | ⬜ **recomendado** |

**Clonar de ElevenLabs ou Google está fora.** Termos dos dois proíbem alimentar
outro motor, e as vozes são licenciadas de locutores reais. E o argumento se
desfaz sozinho: a única razão de clonar é não pagar, e no Google não pagar já é
o caminho oficial (1M chars/mês grátis no Chirp 3 HD, sem expirar).

**Recomendação:** F2.4. ~$50 a $200 uma vez, com cláusula de uso sintético
perpétuo. A gravação vira `ref_audio` travado, o Omni gera as horas todas de graça,
e a MESMA voz fala PT e ES. É o único caminho que entrega "voz boa" e "voz nossa"
ao mesmo tempo.

---

# 🟢 F3 — Infra de GPU (validada 03/08)

Divisão decidida com número medido, não palpite:

| Máquina | RTF | Papel |
|---|---|---|
| VPS Hetzner (CPU, 16 vCPU) | 10,6 | Kokoro e lotes leves. Grátis, já paga |
| **Lightning T4** (79h grátis) | **1,33** | 🔬 **laboratório**: gerar, ouvir, ajustar |
| **RunPod RTX 3090** ($0,22/h) | **0,34** | 🏭 **linha de montagem**: lotes grandes |

- Custo de lote no RunPod: **$0,075 por hora de áudio**. As 130h do Spurgeon
  em PT+ES sairiam por ~$10.
- Studio `fabrica-vozes` com ambiente já instalado no disco persistente.
  Driver em `scratchpad/lit.py` (start / run / up / down / stop).
- [ ] **F3.1 — Gabriel:** conferir o billing do Lightning. Ao ligar o Studio eu
      setei `auto_shutdown_time` e a API avisou que isso converte de grátis pra pago.
      Revertí pro padrão da conta (600s), mas não consigo ler o flag pela API.
      Se tiver ficado pago, apagar o Studio que eu recrio sem tocar em timer.

---

# 🟡 F4 — Fábrica de shorts (frente aberta 07/08)

Pesquisa e desenho completo em [`12_FABRICA_SHORTS.md`](12_FABRICA_SHORTS.md).

Resumo: temos vantagem injusta (transcrição word-level + render + OAuth já
existem). Pipeline de 6 estágios desenhado. ~340 shorts possíveis do acervo atual.

| # | Item | Estado |
|---|---|---|
| F4.1 | Pesquisa de mecânica viral + APIs | ✅ 07/08 |
| F4.2 | Gates: canal (novo vs Spurgeon), visual, cadência | ⬜ Gabriel |
| F4.3 | Credenciais TikTok + Meta (semanas de review, disparar JÁ) | ⬜ Gabriel |
| F4.4 | `mine_clips.py` + composição Remotion 9:16 + piloto de 5 | ✅ 17/08 |
| F4.5 | Publicação Shorts (API já pronta) + fila | ⬜ Claude (bloqueado pelo I1) |

**F4.4 construído e verificado (17/08):**
- `remotion/mine_clips.py` — minerador LLM (gemini-2.5-flash): frases numeradas
  com timestamp → clipes por ÍNDICE de frase (timestamp nunca vem do LLM) +
  reparo determinístico de duração no fim do clipe. Salva `clips_meta.json`
  na pasta do sermão no R2, com word-level re-baseado por clipe.
- `remotion/src/.../ShortSermon.tsx` — composição `Short-Sermon` 1080x1920:
  hook card 2,5s (Georgia + filetes dourados) → karaokê 3-4 palavras/grupo,
  palavra atual dourada com glow, busto + catedral + atribuição. Duração via
  `calculateMetadata` medindo o áudio.
- `remotion/render_short.py` — corta o master (ffmpeg, fade 0,15s), monta props,
  renderiza local (~1 min/short) e sobe pra `renders/spurgeon_shorts/NNNN_cXX.mp4`.
- Piloto: 5 shorts (0001 c01-c03, 0002 c01-c02) no R2 aguardando aprovação.
- 🧨 Mina nova: CSS global do projeto zera margens de `<span>` → espaçamento de
  legenda karaokê tem que ser flex `columnGap`, nunca margin; e `scale()` em
  palavra ativa invade o gap (usar glow, não scale).

---

# 🟡 F5 — Canal de música instrumental cristã (pesquisado 16/08)

Pesquisa completa em [`13_CANAL_MUSICA.md`](13_CANAL_MUSICA.md).

Resumo: **o mais fácil de produzir e o mais arriscado de sustentar.** Render é
ffmpeg puro, e a esteira multi-canal já cobre upload/agendamento. O risco está
em licença (worship moderno tem dono; a saída é hino em domínio público) e na
política de conteúdo inautêntico do YouTube, que demonetizou boa parte dos
canais de música por IA desde o fim de 2025.

| # | Item | Estado |
|---|---|---|
| F5.1 | Pesquisa de licença, monetização e caminhos | ✅ 16/08 |
| F5.2 | Gate: fazer piloto de 3 faixas antes de montar canal | ⬜ Gabriel |
| F5.3 | Curadoria de hinos PD + prova de licença arquivada | ⬜ |
| F5.4 | Assinatura Suno Pro (free NÃO dá direito comercial) | ⬜ Gabriel |

---

# ⚫ Backlog (não começar sem confirmação)

- Funil: `mananciall.org/go` ainda é placeholder (domínio na Vercel, não CF)
- Fábrica de shorts (cortes verticais → Insta/TikTok)
- Migrar estado do agendador (JSON no R2) → Teable
- Derrubar a VPS antiga da Hostinger (`187.127.44.153`)
- Trocar transcrição de AssemblyAI → Groq
- Consertar a tabela `tasks` no Teable (item 1.6 do `04_ROADMAP.md`)
- 51 volumes do Spurgeon ainda por extrair
- Generalizar `CHANNEL_PREFIX` (hardcoded em 4 pontos) pra esteira servir N canais

---

# 🧨 Minas aprendidas nesta rodada

| Mina | Onde morde |
|---|---|
| **OAuth em "Testing" mata o refresh token em 7 dias** | Qualquer canal novo. Publicar o app é passo obrigatório, não opcional |
| **Kokoro cola ~1,1s de silêncio em CADA ponta do áudio** | Emendar trechos sem aparar dá pausa de ~2,6s por mais que se baixe o silêncio inserido |
| **`instruct` do OmniVoice é vocabulário fechado (23 itens)** | Não existe controle de emoção. Adjetivo livre levanta `ValueError` |
| **`ref_text` do OmniVoice é OPCIONAL** | Ele transcreve a referência sozinho com Whisper. A regra antiga de "transcrição exata" não existe mais |
| **Lightning: `auto_sleep_time` converte Studio de grátis pra pago** | Nunca tocar nesse campo. O default da conta (600s) já basta |
| **Lightning não deixa criar venv** (só o conda padrão) | E o `torchaudio` pré-instalado vem quebrado contra o torch da máquina |
| **`datasets` 5.x exige `torchcodec`** (que exige libs do FFmpeg) | Contornar com `Audio(decode=False)` + `soundfile` |
| **MLS entrega falas agrupadas por locutor** | Varrer o stream em ordem devolve 1 voz. Precisa `shuffle(buffer_size=3000)` |
| **VoxPopuli não tem português** | É parlamento europeu. Pra PT o caminho é o MLS |
| **Git bash mastiga path absoluto** (`/teamspace` → `C:/Program Files/Git/...`) | Usar `MSYS_NO_PATHCONV=1`, e no SDK do Lightning usar path relativo |
