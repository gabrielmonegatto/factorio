# 🗺️ ROADMAP ATIVO — frentes em andamento

> Quadro vivo. Atualizado: 04/08/2026.
> Regra: item só sai daqui com verificação real (comando rodado, número medido).

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

- [ ] **P0.5** Health check diário: se `schedule_channel.py` sair com erro, OU se
      passarem 48h sem vídeo novo agendado, dispara webhook no Discord (#fabrica).
      É o item 1.3 do `04_ROADMAP.md`, que agora deixou de ser "nice to have".

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
| F4.4 | `mine_clips.py` + composição Remotion 9:16 + piloto de 5 | ⬜ Claude |
| F4.5 | Publicação Shorts (API já pronta) + fila | ⬜ Claude |

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
