# 🎞️ ÂNCORAS VISUAIS — biblioteca própria de micro-clipes gerados por IA

> Pesquisa de 22/08/2026 (4 frentes paralelas: throughput medido, técnicas de
> consistência, quem produz em escala, e o nicho cristão).
> Origem: o layout de tela dividida dos shorts (âncora em cima, legenda no meio,
> busto embaixo) pede um acervo próprio de micro-clipes de 5-10s.
> Regra desta pesquisa: número sem fonte primária não entrou. O que é estimativa
> está marcado como estimativa.

---

## 1. A tese

Short de sermão prende pelo OUVIDO. O visual não precisa entreter, precisa
**impedir o scroll**. É a função do "retention footage": movimento contínuo e
previsível na parte superior da tela, enquanto a frase carrega o peso.

Referência que o Gabriel trouxe: **@themindsetbrasil** (779 mil seguidores).
O formato é sempre idêntico e o acervo é rotacionado. Só que o banco dele é
**footage de celebridade e cinema** (o post de 21/08 é sobre Keanu Reeves):
material de terceiro, com direito autoral, e com uma estética que não serve a
um canal de Spurgeon. **O que se copia dele é o mecanismo, nunca o acervo.**

O mesmo vale pro Drive de clipes de filme/desenho que já existe: serve a outros
canais, não a este.

---

## 2. O achado que decide a arquitetura

**A consistência é ganha na IMAGEM, não no vídeo.**

O ablation do paper *Lights, Camera, Consistency* (arXiv 2512.16954) mede:
tirar o seed frame de imagem derruba a consistência de personagem de
**7,99 → 0,55**. Tirar só o character sheet: 7,99 → 5,78.

Isso bate com o que TODO produtor sério faz (§4): gera e aprova o **still**
primeiro, e o modelo de vídeo só anima o que já foi aprovado. Text-to-video
puro só se justifica quando não há personagem nem cenário recorrente.

Consequência prática: **iterar em imagem custa centavos e segundos; iterar em
vídeo custa dólares e minutos.** Todo o desenho abaixo é para empurrar o
descarte para a etapa barata.

---

## 3. Descartar É o trabalho (a métrica que ninguém conta)

| Caso | Gerações : aproveitado | Fonte |
|---|---|---|
| Paul Trillo, clipe Washed Out (Sora) | ~700 → 55 = **8%** | No Film School |
| PJ Accetturo, anúncio Kalshi (Veo 3) | 300-400 → 15 = **~4%** | Business Insider |
| Jon Erwin, *House of David* S2 (Amazon) | "20 vezes por plano" = **5%** | VP Land |
| Coca-Cola 2025 (Secret Level) | 70.000 clipes → ~20 planos | VP Land / TheWrap |

**Banda de planejamento: 12:1 a 25:1.** Para 40 clipes bons, planeje ~600 gerações.
O caso da Coca (3.500:1) é outlier de peça-bandeira, não serve de base.

Quem reduz descarte não acerta mais — **torna o descarte barato**:
1. Imagem antes de vídeo (a regra nº 1).
2. Pass rápido (Lightning/GGUF) só pra achar composição e seed; só a vencedora
   vai pra resolução cheia.
3. Evitar estruturalmente o que o modelo erra (a Coca fugiu de lip-sync usando
   narração; aqui: **sem rosto, sem texto na imagem, sem mãos em close aberto**).
4. Nunca fazer upscale antes de selecionar.

⚠️ **Blogspam:** existe uma rede de sites gerados por IA circulando números de
aparência citável e sem fonte primária ("3 gerações por plano usável",
"164 clipes → 41 keepers", "US$ 315 por minuto"). Foram rastreados e não
existem. Se aparecerem em material nosso, vieram daí.

---

## 4. Quem produz de verdade, e com que stack

| Quem | Escala | Stack | Mecanismo de consistência |
|---|---|---|---|
| **Gossip Goblin** (Zack London) | 600M+ views, longa nos cinemas 30/10/2026 | Midjourney v7 (sref + códigos) → Kling i2v | 400 prompts / 1.600 imagens só pros rostos. **90% da cor cozida na imagem** antes de animar |
| **PJ Accetturo** | anúncio Kalshi, US$ 2.000, 1 pessoa, 2-3 dias | Veo 3 + Gemini pros prompts | Cada prompt redescreve tudo do zero |
| **Neural Viz** (Josh Kerrigan) | perfil na Wired | Midjourney → Runway/Kling + Act-One | Desenhou um mundo que **esconde** o que o modelo erra |
| **Sneaky Robot** | workflows públicos | Flux/Z-Image still + **Wan 2.2** | **FLF2V** |
| **Mickmumpitz** | nodes no GitHub | ComfyUI + Blender pré-viz | LoRA a partir de turnaround |
| **Bilawal Sidhu** | — | greybox 3D → "reskin" por IA | Geometria determinística fora do modelo |
| **Secret Level** (Coca-Cola) | comercial nacional | ComfyUI em pipeline comercial | 5 especialistas triando 30 dias |

**Os 4 mecanismos de consistência que existem** (intercambiáveis):
treinar LoRA de folha de personagem · still controlado + i2v · condicionamento
por imagem de referência sem treino (sref, PuLID, BindWeave) · geometria em 3D.
O último é o mais confiável e o mais trabalhoso.

**Padrão que se repete e vale pra nós:** *acervo é ativo composto*. O Gossip
Goblin só fez um longa porque acumulou 11 meses de biblioteca. A biblioteca vem
antes do produto.

---

## 5. Custo e throughput (medido)

Preços de GPU conferidos **na API do RunPod em 22/08/2026** (não em blog):

| GPU | VRAM | US$/h |
|---|---|---|
| RTX 3090 | 24 GB | 0,22 |
| **RTX 4090** | 24 GB | **0,34** |
| A40 | 48 GB | 0,35 |
| RTX 5090 | 32 GB | 0,69 |
| A100 80GB | 80 GB | 1,19 |
| H100 SXM | 80 GB | 2,69 |

Tempos medidos por terceiros (InstaSD, Wan 14B I2V 480p, ~20-30 steps):
4090 = 281s/clipe · A100 = 170s · H100 = 85s. Com **LoRA Lightning (4+4 steps)**
+ SageAttention, a estimativa cai pra **90-150s no 4090**.

| Cenário | Clipes 5s / hora | US$/clipe |
|---|---|---|
| RTX 4090 + Wan 2.2 fp8 + Lightning, 480p | **24-40** | ~0,01 |
| RTX 5090, mesma config | 45-80 | ~0,012 |
| H100 + LTX destilado | 80-240 | 0,008-0,025 |

📌 **Contraintuitivo: GPU cara sai MAIS CARA por clipe.** O H100 é 3,3x mais
rápido e custa 5,9x mais. Só se justifica pra 720p (onde o 4090 dá OOM).

📌 **A escolha de MODELO pesa mais que a de GPU:** trocar Wan por LTX muda o
throughput em 10-50x; trocar 4090 por H100 muda 3x.

**Conclusão de custo: uma biblioteca de 300 clipes cabe em ~US$ 5 e uma noite
de máquina.** O gargalo é curadoria humana, não dinheiro nem GPU.

---

## 6. Direção visual PARA ESTE NICHO (a parte que evita prejuízo)

### Gerar: 7 famílias, não figurativas, não narrativas

1. **Luz em espaço sacro** — raio de sol em poeira na nave, vitral no chão, capela vazia
2. **Mar e tempestade** — onda lenta, horizonte de chumbo, farol, chuva na janela
3. **Fogo e vela** — vela solitária, brasa, lamparina apagando, fumaça
4. **Natureza contemplativa** — neblina no campo, trigo ao vento, árvore isolada
5. **Objetos e mãos anônimas** — Bíblia antiga, mãos em oração (fechado, **sem rosto**), corrente rompendo, banco vazio
6. **Arquitetura e caminho** — porta estreita, escadaria de pedra, arco, estrada sob céu carregado
7. **Abstrato texturizado** — partículas de luz, tinta na água, névoa (só como transição)

O vocabulário casa com o próprio Spurgeon (naufrágio, âncora, rocha).

### Evitar (ordem de risco)

| ❌ | Por quê |
|---|---|
| **Rosto de Cristo** | Pivô de toda a rejeição documentada. A tradição reformada (nosso público) já é iconoclasta pelo 2º mandamento antes da IA entrar |
| **Personagens bíblicos "atuando"** | É o que a crítica chama de reduzir a Bíblia a filme de ação |
| **Estética Marvel/videogame** | Alvo nominal dos críticos do *The AI Bible* |
| **Spurgeon falando / "sermão inédito"** | Cruza de estilística pra **fraude** |
| **Fotorrealismo de evento real** | Dispara a obrigação de disclosure do YouTube |
| **Texto dentro da imagem, dedos errados** | Marcador visual nº1 de "slop" |

### Ritmo

Movimento lento, câmera parada ou push-in de 1-2%, paleta dessaturada, sem corte
rápido. **Isso contraria o conselho genérico de Shorts** (cortar a cada 2-3s) e é
proposital: aqui a retenção vem da frase. **É hipótese, não medição — testar A/B.**

### 🔴 O risco de percepção que é específico nosso

Canais clonaram voz e rosto de **John MacArthur** e **Voddie Baucham** publicando
sermões falsos (centenas de milhares de views antes da denúncia). O público
reformado está **em modo de suspeita com canal de sermão sem rosto**. Antídoto:
atribuição visível em cada peça (nome do sermão, ano, domínio público) e nunca
gerar frase que Spurgeon não disse.

---

## 7. Risco de plataforma (YouTube, jul/2026)

Em **16/07/2026** o YouTube endureceu a política de *inauthentic content*.
A primeira categoria desmonetizada é exatamente **"conteúdo genérico, repetitivo
ou baseado em template, com pouca variação, feito com IA"**. Screen Culture e
KH Studio (2M+ inscritos somados) foram **terminados**.

Acumulamos DOIS vetores ao mesmo tempo: *inauthentic* (visual IA em template) e
*reused content* (texto de terceiro em TTS). Defesas obrigatórias:

- **Nunca repetir o mesmo clipe** entre vídeos, nem a mesma sequência de template.
- **Rotação real** entre as 7 famílias visuais.
- **Camada editorial própria**: seleção curatorial do trecho (já temos, é o
  `mine_clips.py`), contexto histórico do sermão, referência bíblica.
- **Disclosure**: marcar a caixa de conteúdo sintético e declarar na descrição
  "visuais gerados por IA; áudio: sermão de C.H. Spurgeon (domínio público)".
  Tecnicamente vela e névoa são isentos (não representam evento real), mas num
  nicho onde a fraude acabou de acontecer, transparência é **ativo de marca**.

---

## 8. A stack recomendada

### Já temos, de graça (nada a contratar)

| Peça | O que é |
|---|---|
| **Worker `factorio-imagens`** | FLUX schnell na Workers AI via binding. 27 assets gerados, 0 falhas (doc 21). **É o nosso gerador de stills.** |
| **`mine_clips.py`** | Já escolhe o trecho; passa a devolver também o CONCEITO VISUAL do clipe |
| **ffmpeg com `lut3d`** | Confirmado local. É o igualador de estilo em lote |
| **RunPod** | Conta ativa, template e endpoint serverless já criados (`remotion/create_runpod.py`) |

### Gates do Gabriel (custam dinheiro ou credencial)

- **Billing no Google AI Studio** — a chave já alcança `nano-banana-pro` e
  `veo-3.1`, mas está **sem cota**. Destrava character sheet de primeira linha.
- **~US$ 5 de RunPod** para o primeiro lote real de vídeo.

### Ordem de construção

1. **Bíblia visual** (`docs/`): JSON versionado com as 7 famílias, o **style block**
   fixo (lente, emulação de filme, paleta, direção de luz) e a lista de proibições.
   *Custo zero, maior ROI de todos.*
2. **Stills em lote** pelo Worker que já existe: ~200 stills, aprovação no olho.
   Aqui mora o descarte barato.
3. **i2v dos aprovados** no RunPod (Wan 2.2 + Lightning), 5s cada.
4. **Loop perfeito de graça:** no FLF2V, subir **a mesma imagem como primeiro E
   último frame**. O clipe fecha sem emenda. Multiplica a reusabilidade.
5. **LUT única + grain** em lote no ffmpeg. É o que faz clipes de origens
   diferentes parecerem um só mundo.
6. **Casamento semântico**: o conceito visual do trecho escolhe o clipe da
   biblioteca. Como nós escrevemos o prompt de cada clipe, **já temos a etiqueta
   perfeita de graça** — é comparação texto-a-texto, custo desprezível.

### O que PULAR (e por quê)

| Pular | Motivo |
|---|---|
| **LoRA de vídeo** (10-20h de GPU) | Quem segura identidade é o frame inicial; em 5s o i2v não tem tempo de derivar |
| **TwelveLabs** | Busca semântica dentro de vídeo. Vale ouro pro acervo NÃO catalogado (o Drive de filmes); é desperdício na biblioteca de IA, onde nós mesmos escrevemos a etiqueta |
| **PuLID/InstantID** | São de rosto. Não temos rosto na tela |
| **Encadeamento longo de clipes** | É onde mora a deriva de cor. Micro-clipe independente não sofre disso — vantagem estrutural do formato |
| **Veo 3.1 Standard em volume** | US$ 3,75 por 5s = US$ 1.125 numa biblioteca de 300. Reservar pros clipes-herói |
| **Comprar pack de b-roll IA** | Nenhum declara modelo, custo ou licença real |

**Regra de bolso:** cada real em **style block + still + LUT** compra mais coesão
do que dez reais em modelo de vídeo mais caro.

---

## 9. Fontes

**Consistência:** [Lights, Camera, Consistency (arXiv 2512.16954)](https://arxiv.org/html/2512.16954v1) ·
[Phantom (arXiv 2502.11079)](https://arxiv.org/html/2502.11079v1) ·
[ComfyUI Wan 2.2 FLF2V](https://comfy.org/workflows/video_wan2_2_14B_flf2v-7016f027bcf1/)

**Throughput:** [InstaSD benchmarks](https://www.instasd.com/post/wan2-1-performance-testing-across-gpus) ·
[Voltage Park](https://voltagepark.com/blog/accelerating-wan2-2-from-4-67s-to-1-5s-per-denoising-step-through-targeted-optimizations) ·
[Morphic](https://github.com/morphicfilms/wan2.2_optimizations/blob/main/blog.md) ·
[lightx2v Wan2.2-Lightning](https://huggingface.co/lightx2v/Wan2.2-Lightning) ·
preços conferidos na API do RunPod

**Produção real:** [PJ Ace sobre o workflow do Gossip Goblin](https://pjace.beehiiv.com/p/gossip-goblin-s-crazy-workflow-for-building-original-worlds-200m-views) ·
[VP Land: House of David S2](https://www.vp-land.com/stories/house-of-david-season-2-used-253-ai-generated-shots-here-s-how-they-did-it) ·
[VP Land: Coca-Cola 70.000 clipes](https://www.vp-land.com/p/coca-cola-s-ai-holiday-ad-how-70-000-generated-clips-built-a-familiar-yet-new-commercial) ·
[No Film School: Paul Trillo](https://nofilmschool.com/ai-music-video)

**Nicho e política:** [YouTube inauthentic content](https://support.google.com/youtube/answer/1311392?hl=en) ·
[YouTube disclosure de conteúdo sintético](https://support.google.com/youtube/answer/14328491?hl=en) ·
[TechCrunch 20/07/2026](https://techcrunch.com/2026/07/20/youtube-clarifies-policies-around-ai-slop-and-upsetting-videos/) ·
[Protestia: sermões falsos de Voddie Baucham](https://protestia.com/2025/05/19/this-youtube-channel-tricks-christians-by-posting-bad-ai-generated-voddie-baucham-sermons/) ·
[The Dissenter: MacArthur falso](https://disntr.com/2025/04/22/fake-youtube-channel-produces-ai-generated-john-macarthur-sermons-racks-up-100s-of-thousands-of-views/) ·
[NPR/Ideastream sobre The AI Bible](https://www.ideastream.org/2025-09-07/fantasy-or-faith-one-companys-ai-generated-bible-content-stirs-controversy)

**Comunidade:** [Discord Banodoco](https://huggingface.co/datasets/Banodoco/discord-archive) ·
[Banodoco Knowledge Base](https://nathanshipley.github.io/banodoco-kb/) ·
[VP Land](https://www.vp-land.com/) · r/comfyui (207k, +75%/ano)
