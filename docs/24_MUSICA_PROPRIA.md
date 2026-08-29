# 24 · Música própria: hinário estilizado vs. louvor original (pesquisa)

**Status:** frente FUTURA, parada até o upgrade pro Premium+ (music rights).
**Data:** 29/08/2026. Fontes no fim; o que não foi confirmado está marcado.

---

## 1. A pergunta do Gabriel e a resposta curta

*"Dá pra pegar hinários e estilizar em piano, violino, clássico, lo-fi?"*

**Com o Lyria 3, não.** Ele aceita **só texto e imagem** como entrada. Não tem
cover, style transfer, continuação, MIDI nem humming (model card oficial + doc
do Gemini API, que diz explicitamente que continuation/cover/remix não são
suportados). Pedir "Amazing Grace em lo-fi" devolve **uma música lo-fi com clima
de hino, que não é Amazing Grace** — e diferente a cada chamada, porque não há
seed nem determinismo.

**A ideia se parte em dois produtos diferentes:**

| | o que é | motor | status |
|---|---|---|---|
| **A. Hinário estilizado** | a melodia REAL do hino, reinstrumentada | MIDI em DP + Stable Audio 3.0 (ou instrumento virtual) | viável, exige curadoria jurídica |
| **B. Louvor original** | música nova, letra nossa, no espírito do hino | **Lyria 3 faz hoje** | viável, mais seguro |

## 2. A descoberta que muda o produto B

O Lyria 3 **canta**: aceita letra própria com tags `[Verse]`, `[Chorus]`,
`[Bridge]`, letras cronometradas, controle de voz (gênero, tessitura tipo
barítono/soprano, textura tipo gravelly/soulful/breathy) e **8 idiomas,
incluindo português**. Instrumental é opt-in ("Instrumental only, no vocals").

Isso torna o produto B mais interessante que o A: **louvor autoral do
ecossistema**, com letra escrita por nós (ou minerada dos próprios sermões do
acervo), em vez de releitura do hino de outro. Sai do território de "cover de
IA" e entra em obra própria — que é exatamente o que o direito e a política de
plataforma premiam.

Parâmetros: Clip 30s fixo (US$ 0,04) · Pro até ~3 min (US$ 0,08) · MP3, WAV no
Pro · SynthID embutido, não removível · sem negative prompt, sem seed.

## 3. As armadilhas jurídicas (a parte que decide a frente)

### 3a. Domínio público confirmado
Isaac Watts (†1748), Charles Wesley (†1788), John Newton (†1807), Fanny Crosby
(†1915). Letra E melodia originais livres nos dois países. "Amazing Grace":
texto 1779, melodia "New Britain" 1829 — DP.

Regra: **Brasil** = 70 anos da morte do autor (Lei 9.610/98), contados do 1º de
janeiro seguinte, e do ÚLTIMO coautor. **EUA** = 95 anos da publicação; em
01/01/2026 caiu tudo publicado até 1930. **DP nos EUA não implica DP no Brasil**
— critérios diferentes. Canal global passa pelo mais restritivo.

### 3b. 🧨 ARRANJO TEM DONO (Lei 9.610, art. 14)
> "É titular de direitos de autor quem adapta, traduz, arranja ou orquestra obra
> caída no domínio público, não podendo opor-se a outra adaptação (...) salvo se
> for cópia da sua."

Podemos arranjar o hino livremente e o arranjo é NOSSO. Não podemos copiar o
arranjo de outro. **Consequência prática: MIDI de hinário moderno carrega a
harmonização do editor, não o hino de 1780.** Só usar fonte com DP declarado
por hino.

### 3c. 🧨 GRAVAÇÃO É DIREITO SEPARADO
Composição em DP ≠ fonograma em DP. Gravação nova de hino livre nasce
protegida. **Nunca alimentar modelo nenhum com áudio de gravação de terceiro**,
nem de hino em DP. É a armadilha que gera processo.

### 3d. 🧨 Hinos que parecem antigos e não são
- **"How Great Thou Art"** (Hine, 1949/53): **protegida até 2059**. Está em
  quase todo hinário protestante.
- **"Great Is Thy Faithfulness"** (1923): DP nos EUA desde 2019; **status no
  Brasil NÃO verificado** (lá conta a morte dos autores).

### 3e. 🧨 Traduções em português são obras derivadas
Harpa Cristã, Cantor Cristão, Novo Cântico: as traduções têm autor e prazo
próprios, independentes do original em inglês. **Nenhuma foi verificada.**
Pendência aberta se o canal for em português com letra cantada.

## 4. Risco de plataforma (o mais provável de nos atingir)

O YouTube renomeou "Repetitious content" para **"Inauthentic content"** em
15/07/2025. Texto oficial: viola a política **"AI-generated content made with
generic or unoriginal templates"** que dá **"the impression of mass production
without adding the creator's original, authentic insights"**.

Um canal com 200 vídeos "[Hino X] em lo-fi", mesma arte e mesma descrição, é o
alvo desenhado dessa política. **O risco não está na IA, está na
industrialização visível.** Mitigação: variar template, arte e descrição; e ter
mão humana demonstrável no arranjo.

Música de IA **precisa ser divulgada** como conteúdo sintético (consta na tabela
oficial de exemplos). Fontes secundárias dizem que declarar não reduz alcance
nem monetização — **não confirmado em fonte oficial**.

**Agravante:** é amplamente reportado que o U.S. Copyright Office não registra
obra puramente gerada por IA (falta autoria humana). Se verdade, **nossa faixa
100% IA pode não ter proteção pra opor a quem a reivindicar no Content ID**.
Reforça a regra: o arranjo precisa ter mão humana documentada.

## 5. Se a frente for tocada, o caminho

1. **Melodia vem de MIDI em DP**, nunca de gravação. Fonte mais limpa:
   **Open Hymnal Project** (openhymnal.org), único que coloca o próprio trabalho
   em domínio público; PDF, MIDI, MP3, ABC. Cyber Hymnal serve com atribuição.
   IMSLP e Hymnary indexam material moderno protegido junto — verificar por hino.
2. **Reinstrumentação: Stable Audio 3.0.** Único que junta audio-to-audio real,
   pesos abertos, treino em dados licenciados e licença comercial clara (até
   US$ 1M de receita). Ler a Community License linha a linha antes.
3. **Descartados:** MusicGen-melody (pesos CC-BY-NC, não comercial), Udio
   (desativou download), Suno (sem API oficial; troca de modelos pelo acordo
   Warner), ElevenLabs Music (conditioning parece aceitar só `song_id` interno).
4. **Lyria fica no produto B**: louvor original, letra nossa, cantado.

## 6. Por que está parada

Music rights só existem no **Premium+**. A entrada decidida em 25/08 foi o
Premium mensal (doc 23 §8), e a prioridade é liberar os 673 shorts. Enquanto
isso: **não gerar trilha no Lyria**; shorts seguem com as 4 faixas worship já
licenciadas dos longos.

## 7. Não confirmado (não decidir em cima disso)

- Sample rate do Lyria: fontes oficiais divergem (48 kHz vs 44,1 kHz).
- Limite de 30s do Lyria dentro da Magnific (doc devolveu 403).
- Se a ElevenLabs Music aceita upload de áudio externo pra conditioning.
- Licença completa do Stable Audio 3.0 (lidos só resumos de imprensa).
- Status DP no Brasil de "Great Is Thy Faithfulness" e dos hinários brasileiros.
- Documento primário do USCO sobre não registrabilidade de obra de IA.
- Qualquer caso documentado de Content ID reivindicando hino em DP.

**Fontes:** ai.google.dev/gemini-api/docs/music-generation · model card Lyria 3
Pro · cloud.google.com/blog (prompting guide) · stability.ai (Stable Audio 3.0)
· facebookresearch.github.io/audiocraft (MusicGen) · elevenlabs.io/docs ·
planalto.gov.br/ccivil_03/leis/l9610.htm · web.law.duke.edu/cspd/publicdomainday/2026
· howgreatthouarthymn.com · openhymnal.org · hymntime.com/tch ·
support.google.com/youtube/answer/1311392 · support.google.com/youtube/answer/14328491
