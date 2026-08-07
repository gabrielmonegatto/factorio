# ✅ CHECKLIST — Canal de narração bíblica

> Segunda frente de canal dark. Reaproveita a esteira do Spurgeon
> (narrar → legendar → renderizar → thumb → publicar), mas o produto é outro:
> catálogo fechado e finito em vez de fluxo contínuo de sermões.
> Criado: 03/08/2026.

---

## BLOCO 0 — O gate que mata o canal se for pulado

**Escolher a tradução. Isto vem antes de qualquer linha de código.**

A Bíblia não é domínio público: as **traduções** é que são obras protegidas, e as
modernas têm dono ativo que emite claim. Narrar a Bíblia inteira numa tradução
protegida é o jeito mais rápido de perder o canal depois de 90 horas de áudio prontas.

| Situação | Traduções |
|---|---|
| 🚫 **NÃO usar** (protegidas, titular ativo) | NIV, ESV, NLT, NASB, NKJV, CSB, MSG, AMP |
| ✅ **Domínio público (EN)** | KJV (1611/1769), ASV (1901), World English Bible (WEB), Douay-Rheims, Young's Literal |
| ✅ **Domínio público (PT)** | Almeida 1819 e derivadas livres. ⚠️ ARC e ACF têm titular (SBB / Trinitariana), NVI é protegida |
| ✅ **Domínio público (ES)** | Reina-Valera 1909. ⚠️ RV1960 é protegida (Sociedades Bíblicas Unidas) |

**Recomendação EN: KJV.** É o que a audiência de narração bíblica realmente procura
(o volume de busca não é comparável) e é domínio público nos EUA.
*Ressalva honesta:* no Reino Unido a KJV é Crown copyright perpétuo via letters patent.
Na prática não há enforcement no YouTube, mas a alternativa de risco zero existe:
**WEB**, inglês moderno, domínio público sem asterisco nenhum.

- [x] **0.1** ✅ **MARTELO 03/08/2026: KJV *e* WEB, as duas no mesmo canal.**
  A WEB entra como seguro: se a Crown copyright da KJV der ruído algum dia,
  metade do catálogo já está limpa e o canal não para.
- [ ] **0.2** Baixar o texto de fonte com procedência declarada e guardar a prova da licença junto do corpus
- [ ] **0.3** Registrar a decisão aqui com data

### Consequência da decisão 0.1 (não pular)

Duas traduções dobram o corpus pra **~186 horas / 200 a 240 vídeos** e criam um
risco novo: Gênesis KJV e Gênesis WEB são ~85% do mesmo texto, mesma duração,
mesma capa. Isso tem cara de reupload pro sistema do YouTube.

**Mitigação obrigatória: voz diferente por tradução.** KJV em voz britânica (o texto
é jacobino, assenta), WEB em voz americana (inglês moderno). Separa os dois aos
olhos da plataforma e dá ao ouvinte um motivo real de escolher um ou outro.
Título e capa também precisam marcar a tradução de forma inequívoca.

---

## BLOCO A — Decisões de formato (definem o resto)

O KJV tem **66 livros, 1.189 capítulos, ~783 mil palavras**. A 140 palavras por minuto
isso é **~93 horas de áudio**. O recorte muda tudo a jusante.

| Recorte | Nº de vídeos | Leitura |
|---|---|---|
| Por capítulo | 1.189 | Inviável de gerir, e cada vídeo é curto demais pra reter |
| Por livro | 66 | Alguns passam de 4h (Salmos, Isaías, Jeremias) |
| **Por bloco de ~1h** ✅ | **~100 a 120** | Casa com o consumo real (sono / estudo / rotina) e mantém o livro coeso |

- [ ] **A1** Fechar o recorte (recomendado: bloco de ~1h respeitando fronteira de capítulo, nunca cortando no meio)
- [ ] **A2** **Ler ou não o número do versículo em voz alta.** Decisão de produto, não técnica: a audiência de sono/descanso odeia, a de estudo precisa. Se for atender as duas, são duas playlists a partir do MESMO áudio-base, não dois canais
- [ ] **A3** Ordem de publicação: canônica (Gênesis → Apocalipse) ou por demanda (Salmos, Provérbios, João e Gênesis primeiro). A segunda entrega tração mais rápido
- [ ] **A4** Nome, identidade visual e descrição do canal

---

## BLOCO B — Voz e áudio

- [ ] **B1** Escolher **duas** vozes EN no Kokoro, uma por tradução (ver consequência da decisão 0.1):
  uma britânica pra KJV (`bm_lewis` ou `bm_daniel`) e uma americana pra WEB
  (`am_onyx`, `am_michael` ou `am_fenrir`).
  **Nenhuma pode ser `bm_george`**, que é a voz do canal Spurgeon: dois canais com a
  mesma voz viram o mesmo canal aos ouvidos de quem assiste os dois.
  *Amostras geradas 03/08 (Salmo 23, speed 0.85) em `/srv/factorio/data/vozbiblia/` na VPS.*
- [ ] **B2** Travar `VOICE` + `SPEED` num config do canal e **nunca mais mexer**. 186 horas de áudio com timbre trocado no meio é retrabalho total
- [ ] **B3** Regra de normalização de número. `normalize_text` resolve numeral solto, mas referência bíblica ("Salmos 27:1") precisa de tratamento próprio antes de virar áudio
- [ ] **B4** Medir o RTF do Kokoro na VPS e estimar o lote. Se der pra rodar de graça na CPU ao longo de dias, **não gasta GPU nenhuma aqui**
- [ ] **B5** Amostra de QA: gerar 3 blocos de partes diferentes (poesia, genealogia, narrativa) e ouvir. Genealogia é o teste duro, é onde TTS quebra

### Interpretação: o teto e a única alavanca (medido 03/08)

Kokoro não tem controle de emoção, só velocidade. E o modo design do OmniVoice,
que parecia a saída, **também não tem**: o campo `instruct` aceita só 23 atributos
objetivos (gênero, faixa etária, altura de voz, sotaque, whisper) e levanta erro
em qualquer adjetivo de interpretação. "Calmo", "solene", "autoritário": todos rejeitados.

Ou seja, os dois motores têm o mesmo teto. **A única alavanca real de interpretação
está fora do modelo: engenharia de pausa.** Narrar versículo a versículo e costurar
com ~0,55s de silêncio entre eles. O ouvido lê como respiração e intenção, não como
lentidão, e rende muito mais que baixar a velocidade.

### ✅ REGRA DE PAUSA DO CANAL (travada 03/08/2026)

```
1. cortar o texto SÓ em ponto final (nunca em ':' ou ';' — vira picotado)
2. narrar cada trecho separado
3. APARAR o silêncio das pontas de cada trecho:
   ffmpeg -af "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05,
               areverse,silenceremove=...,areverse"
4. emendar com 0,75s de silêncio entre os trechos
```

**MINA que custou 3 tentativas:** o Kokoro entrega cada trecho com ~1,1s de silêncio
colado em CADA ponta. Emendar sem aparar soma padding dele nos dois lados mais o meu,
e o intervalo real vira ~2,6s por mais que eu baixe o meu número. Medido via
transcrição word-level do Groq: baixar meu silêncio de 0,55s para 0,18s mexeu no
intervalo real de 2,96s para apenas 2,58s. Depois de aparar, o mesmo trecho com
0,75s inseridos mede 1,12s de intervalo real e o áudio inteiro fica MAIS CURTO
que a leitura corrida (29,9s contra 31,5s).

Vale pros três idiomas: o padding é do TTS, não do texto.

*Nota de método: timestamp por palavra do Whisper engole silêncio curto. Para
intervalo abaixo de ~0,3s o número confiável é a duração total, não o gap.*

- [x] ✅ **Voz EN 03/08: `am_michael`, speed 0.80, pausa 0,75s** (aprovado no ouvido)
- [x] ✅ **Ordem 03/08: KJV primeiro.** Com só uma tradução no ar, a regra de
  voz-por-tradução não morde ainda, então o `am_michael` vai na KJV. A segunda voz
  só vira decisão quando a WEB entrar.
- [ ] Se for pro Google Chirp 3 HD (ver Bloco E), reescolher a voz lá

---

## BLOCO E — Qual motor de TTS (decisão pendente)

Levantamento de 03/08. A KJV tem ~4,4 milhões de caracteres.

| Motor | $/1M chars | KJV inteira | Voz é nossa? |
|---|---|---|---|
| Kokoro (local) | $0 | $0 | não, catálogo aberto |
| Google WaveNet | $4 | $18 | não |
| **Google Chirp 3 HD** | $30 | **$132**, ou **$0** na cota grátis | não |
| Google Studio | $160 | $704 | não |
| ElevenLabs (faixas reais) | $120 a $240 | $528 a $1.056 | não |
| OmniVoice + locutor contratado | $0 + cachê único | ~$50 a $200, uma vez | **sim, pra sempre** |

**O Google dá 1M de caracteres/mês no Chirp 3 HD sem expirar.** A KJV cabe em
5 meses de cota grátis, com licença comercial limpa. Canal de Bíblia não tem pressa.

**Clonar voz de Google ou ElevenLabs está fora.** Os termos dos dois proíbem usar
o áudio gerado pra alimentar outro motor, e as vozes são licenciadas de locutores
reais. Além disso o argumento se desfaz sozinho: a única razão de clonar é não pagar,
e no Google não pagar já é o caminho oficial.

**Divisão recomendada:** Bíblia usa Google (voz de catálogo é irrelevante quando
ninguém associa o Salmo 23 a um timbre). Spurgeon usa voz própria clonada no Omni,
porque lá a voz É a marca.

- [ ] **E1** Conferir os preços na página oficial (`cloud.google.com/text-to-speech/pricing`); os números acima vieram de agregadores
- [ ] **E2** Gerar o mesmo Salmo 23 no Chirp 3 HD e comparar com o `am_michael` no ouvido
- [ ] **E3** Bater o martelo: Kokoro grátis e já montado, ou Google grátis-na-cota e melhor

---

## BLOCO C — A armadilha do "conteúdo reutilizado"

Canal que é só TTS lendo texto de domínio público sobre imagem parada é **exatamente**
o arquétipo que a política de conteúdo reutilizado do YouTube existe pra barrar.
O canal roda, mas a monetização é negada. O que separa um do outro é camada original.

- [ ] **C1** Visual original de verdade (não banco de imagem genérico repetido 120 vezes)
- [ ] **C2** Trilha: composta, licenciada com prova, ou nenhuma. Nunca "achei no YouTube"
- [ ] **C3** Camada editorial própria: introdução falada de contexto do livro, estrutura de capítulos, timestamps curados
- [ ] **C4** Ler a política vigente antes de submeter à monetização, não depois

---

## BLOCO D — Publicação (herda do Spurgeon)

- [ ] **D1** Canal criado + OAuth (`auth_youtube.py`) — **Gabriel**
- [ ] **D2** Generalizar o `CHANNEL_PREFIX` (hoje hardcoded em 4 pontos da esteira)
- [ ] **D3** Thumbnail template do canal
- [ ] **D4** QR / funil apontando pro `/go` com `v=` próprio deste canal
- [ ] **D5** Fila no Teable com o corpus inteiro fatiado em blocos
- [ ] **D6** **1 vídeo publicado de verdade**, com gate humano
- [ ] **D7** 3 vídeos limpos seguidos = estável, aí sim automatiza

---

## Por que este canal é mais fácil que o Spurgeon

O corpus é **fechado, conhecido e já estruturado**. Não tem extração de volume,
não tem formatação de capítulo pra consertar, não tem tradução, não tem seleção
editorial de qual sermão entra. É pegar um texto canônico e fatiar.

O trabalho todo está em três lugares: a **decisão de licença** (Bloco 0), a
**consistência ao longo de 93 horas** (Bloco B) e a **camada original** que separa
canal monetizável de spam aos olhos da plataforma (Bloco C).
