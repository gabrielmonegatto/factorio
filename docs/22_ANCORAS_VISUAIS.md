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

### Gates do Gabriel

**Nenhum.** RunPod já tem crédito e a Cloudflare gera os stills de graça.

❌ **Google AI Studio foi DESCARTADO** (decisão de 22/08). A chave alcança
`nano-banana-pro` e `veo-3.1` mas está sem cota, e **não faz falta**: o
character sheet que justificaria o nano-banana serve pra manter um
**personagem** consistente, e a nossa direção visual não tem personagem
nenhum (sem rosto é regra do nicho, §6). Fica como opção futura se a
qualidade do FLUX limitar, não como pré-requisito.

### ✅ Validado em 22/08/2026 (teste real, não estimativa)

8 stills gerados pelo Worker `factorio-imagens` (FLUX schnell) cobrindo as 7
famílias, com o style block fixo:

| Métrica | Resultado |
|---|---|
| Tempo | **2 a 8,5s por still** (7 stills em ~30s) |
| Custo | **zero** (Workers AI, sem billing) |
| Aproveitamento | **6 de 8** direto |
| Corrigir | `mist` saiu claro demais, destoa da família (conserto: prompt ou LUT) |
| Descarte | `ink` saiu fraco, quase invisível |

**A tese se confirmou:** ~75% de aproveitamento na etapa de imagem, contra os
4-8% documentados na etapa de vídeo (§3). É exatamente por isso que o descarte
tem que morrer aqui. Resolução de saída: 1024x1024, que cobre com folga a faixa
da âncora (1080x806 no layout 9:16).

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

## 8b. 🧨 A economia de neurônios da Workers AI (medido em 22/08)

"Grátis" tem teto diário: **10.000 neurônios/dia**, no plano Free E no Paid.
Estourou, todo modelo devolve `4006` e o Worker responde 500. Foi o que
aconteceu depois dos 42 stills + testes.

| Modelo | Neurônios/imagem 1024² | Grátis por dia | Imagens por US$ 1 |
|---|---|---|---|
| `flux-1-schnell` (4 steps) | ~58 | **~173** | **~1.580** |
| `leonardo/phoenix-1.0` | ~2.370 | ~4 | ~38 |
| `leonardo/lucid-origin` | ~2.844 | **~3** | ~32 |

Custo acima da cota: **US$ 0,011 / 1.000 neurônios**, e exige o
**Workers Paid (US$ 5/mês)** na conta `eternall`.

**Leitura:** FLUX schnell é praticamente ilimitado pro nosso volume (173/dia
de graça). Os modelos da Leonardo são ~50x mais caros em neurônio, mas
entregam pintura de verdade — e a US$ 0,03 por imagem, um ensaio de 40 cenas
custa **US$ 1,25**. O gate não é o consumo, é a assinatura de US$ 5/mês.

⚠️ `flux-2-dev` e `flux-2-klein` continuam **inacessíveis pelo Worker**: exigem
`multipart` e o FormData pelo binding é rejeitado (mina do doc 21, confirmada
de novo hoje). Os da Leonardo aceitam JSON normal.

---

## 8c. ↩️ REVERSÃO: os ensaios dos pregadores (decidido 22/08)

O §6 diz "sem personagem". **Isso mudou.** O Gabriel propôs ensaios completos
dos pregadores em estilo ILUSTRADO — Spurgeon e Moody em situações cotidianas
(andando, pensando, pregando, comendo, lendo, orando, chorando).

**Por que o risco do §6 NÃO se aplica aqui.** A rejeição documentada tem dois
alvos, e nenhum é este:
1. **Rosto de Cristo** — não é o caso. Spurgeon e Moody são homens, não a divindade.
2. **Fraude com pregador** — os casos (MacArthur, Baucham) eram voz clonada
   dizendo o que a pessoa nunca disse. Aqui é texto real, de domínio público,
   de homens mortos há 130+ anos.

E a própria pesquisa registrou que **estilo pictórico sinaliza "isto é arte,
não registro"**, o que derruba de uma vez a obrigação de disclosure (não pode
ser confundido com filmagem real) e a acusação de irreverência. Ou seja:
desenho não é concessão defensiva, é a escolha tecnicamente superior.

**Guarda-corpo que permanece:** nunca fotorrealista a ponto de parecer registro
histórico, e nunca Cristo. A ilustração resolve os dois sozinha.

**Consequência técnica:** agora existe personagem recorrente, então character
sheet e consistência de referência **voltam a valer** (o §8 tinha descartado).
Vantagem nossa: pregador de canal Treasures morreu antes de 1930 por definição
(doc 18), então **sempre existe foto real em domínio público** pra servir de
referência. Não se inventa a cara: parte-se dela.

**Validado hoje:** `leonardo/lucid-origin` com bloco de estilo pictórico
(pincelada texturizada, paleta carvão + âmbar, luz única) entregou exatamente
o registro pretendido na primeira tentativa.

**Valor estratégico:** este acervo é maior que o das âncoras. Serve short,
vídeo longo, thumbnail, capa de livro e a livraria. É a identidade visual da
rede Treasures inteira.

---

## 8d. ✅ MEDIDO NO METAL (22/08/2026) — o pipeline fecha ponta a ponta

Primeiros micro-clipes nossos gerados. Não é mais estimativa.

| Métrica | Valor medido |
|---|---|
| Modelo | `Wan2.2-TI2V-5B-Diffusers` via `WanImageToVideoPipeline` |
| GPU | RTX 4090 (US$ 0,34/h) |
| Config | 61 frames @ 24fps (2,5s), 25 steps, 704x704 |
| Carga do modelo | 45s |
| **Tempo por clipe** | **83,9s** (min 82,0 / máx 86,6 — variação desprezível) |
| **Vazão** | **~43 clipes/hora** |
| **Custo por clipe** | **US$ 0,008** |
| Movimento real | 39 a 58 quadros com mudança, de 61 (conferido por `scene` no ffmpeg) |
| Custo total do aprendizado | US$ 0,64 em 9 rodadas |

**Projeção com número medido:** biblioteca de 300 clipes = **US$ 2,40 e ~7h de
máquina**. Bate com a estimativa da §5. O gargalo é curadoria humana, não custo.

### 🧨 As 7 minas do RunPod (todas custaram rodada; todas viraram trava no script)

| # | Mina | Sintoma enganoso | Conserto no `animar.py` |
|---|---|---|---|
| 1 | **Cloudflare bloqueia User-Agent do urllib** (mesma do doc 21) | 403 em toda mutation; parece chave sem permissão ou falta de GPU | `User-Agent` próprio no `gql()` |
| 2 | API do RunPod é instável | 403 transitório, timeout de leitura, reset de conexão | reprova com espera no `gql()`, ponto único |
| 3 | Ubuntu 24.04 aplica PEP 668 | `pip install` "passa" no pipe e o import quebra depois, já com GPU paga | `--break-system-packages` + **verificação de import antes de gerar** |
| 4 | Pod COMMUNITY às vezes nunca entrega IP público | trava esperando SSH | `subir_pod()` descarta o pod ruim (matando-o) e pede outro |
| 5 | Porta 22 aparece ANTES da chave ser instalada | `Permission denied`, e o script seguia calado | exige `echo PRONTO` autenticado antes de usar o pod |
| 6 | **Sessão SSH cai em trabalho longo** | 33min de geração perdidos, US$ 0,22 no lixo | roda `setsid` solto com log; acompanha por conexões curtas |
| 7 | 5B bf16 a 704px estoura os 24GB no decode do VAE | OOM pedindo 230MB com 22,9GB alocados | `enable_model_cpu_offload()` + `vae.enable_tiling()` + slicing. ⚠️ offload NÃO convive com `.to("cuda")` |

### 🧨 A mina do modelo (custou 1 rodada)

O card do `Wan2.2-TI2V-5B` no HuggingFace mostra `WanPipeline(image=...)`.
**Está errado:** `WanPipeline` é texto-para-vídeo e recusa `image`. O caminho
i2v do Wan 2.2 é o **`WanImageToVideoPipeline` SEM `image_encoder`** (é
`_optional_component`, e o repo do 5B não traz a subpasta; o modo é
`expand_timesteps: true`, declarado no `model_index.json`).
Lição: em modelo novo, conferir `model_index.json` + assinatura da classe no
código-fonte, nunca o card.

Detalhe operacional: neste ambiente o kwarg ainda é `torch_dtype` (não `dtype`).
O script detecta por `inspect.signature` em vez de chutar — chutar errado carrega
tudo em fp32 e estoura a placa.

### Pendências desta frente

- [ ] Gabriel: julgar o ritmo do movimento (sóbrio o bastante pra não competir com a voz?)
- [ ] Subir pra 5s (121 frames): dobra o custo, segue irrisório
- [ ] Ligar `--loop` (primeiro frame = último): já implementado, custo zero, fecha sem emenda
- [ ] Gerar na proporção da faixa da âncora em vez de quadrado
- [ ] LUT única em lote pra igualar as famílias (mar e natureza saem mais claros)

---

## 10. Rodada 2 de pesquisa (22/08, noite): quem faz, quem ensina, e o plano de qualidade

Disparada depois do veredito do Gabriel sobre o piloto: "funcionou, mas ficou
horrível". Três frentes; o detalhe integral está nos relatórios desta seção.

### 10a. Por que o piloto ficou feio (autópsia honesta)

1. **Config fora da spec**: o TI2V-5B só conhece 1280x704 (ou 704x1280).
   Rodamos 704x704 (resolução que o modelo NÃO suporta), com 61 frames
   (nativo: 121) . Steps 25 estavam ok (default oficial do template: 20).
2. **Modelo errado pra resultado final**: NENHUM tutorial sério usa o 5B pra
   entrega. Todos usam o par 14B high/low noise, mesmo quantizado (GGUF Q4/Q5
   roda em 8GB). O 5B é modelo de demo pra hardware fraco.
3. **Zero curadoria**: entregamos 6 de 6. O padrão da indústria é descartar
   12-25 por 1.

### 10b. Consenso de qualidade dos criadores do YouTube (as 8 alavancas)

Extraído de ~20 canais com workflow público (CaoCao2025, Olivio Sarikas,
Next Diffusion, AI2Play, MDMZ, Benji, Curious Refuge, Tao Prompts, PurzBeats
do canal oficial ComfyUI, Endangered AI, e os BR Preguiça Artificial e
Santinello):

1. **Clipe bonito nasce de still bonito** (upscale ANTES de animar: Curious Refuge).
2. **14B, nunca 5B.**
3. **LoRA lightx2v/Lightning com a receita certa**: 8 steps (4 high + 4 low),
   CFG 1, LCM/euler. Defeito conhecido (admitido pelos autores na discussion
   #26): suprime movimento. Conserto publicado (Next Diffusion): tirar a LoRA
   do high, subir high pra 10-20 steps com CFG 3, manter LoRA só no low.
4. **UM movimento por clipe + advérbio de lentidão** ("slowly", "gently").
   Dois movimentos no prompt = morphing. Câmera: "static shot" ou um único
   "slow push-in".
5. **Negative prompt oficial do Wan EM CHINÊS** (o modelo foi treinado assim)
   + extras anti-morphing ("morphing, warping, distortion, flickering").
6. **Loop de verdade = FLF2V com a mesma imagem nas duas pontas** + remover o
   frame final duplicado. No Kling: aba Frames, start = end (método AI2Play).
   Ping-pong de CapCut denuncia em fumaça/água.
7. **Pós obrigatória mata o "plástico de IA"**: interpolação RIFE (16→32fps),
   upscale, e film grain sutil (~15-20%, size ~0.4) ou filtro NTSC-RS por cima.
8. **Curto e emendado**: 81 frames (5s) é o sweet spot; artefato piora com
   duração.

Settings de referência (template oficial ComfyUI, JSON conferido):
5B = 1280x704, 121f, 20 steps, CFG 5, uni_pc, shift 8 ·
14B FLF2V = 81f, 2x KSamplerAdvanced euler 20 steps CFG 4 split no 10, shift 8 ·
14B + Lightning = 4 steps CFG 1 split no 2, shift 5.

### 10c. Ranking de modelos pra I2V atmosférico (evidência, não achismo)

Arena Elo da Artificial Analysis (votação cega, snapshot 22/08): a família
**Hailuo/MiniMax é #2 do mundo** em I2V; **Kling** é tratado pela comunidade
como "o diretor de arte" (atmosfera/câmera, nosso caso exato); Wan open fica
um tier abaixo; **LTX descartado** (Elo ~200 pontos abaixo do Kling 3.0,
apesar da fama de velocidade).

Preço API (fal.ai, verificado): Hailuo 02 768p US$ 0,27/clipe ·
Kling 2.5 Turbo Pro US$ 0,35 · Veo 3.1 Lite US$ 0,15 (não testado em cena
sutil). **300 clipes tudo-API: US$ 81-105.** O Kling expõe "tail image"
(= nosso loop perfeito).

### 10d. Mercado (quem usa banco de clipes no formato @themindsetbrasil)

- Os gigantes do formato usam **stock licenciado**, não IA: rede Motiversity
  (13M+), Lion of Judah (3,5M), Grace for Purpose (3,8M) compram Filmpac
  (~US$ 25/mês) e Artgrid. O mundo "sigma" usa scene packs piratas de filme
  (inviável pra marca séria).
- Onde IA confirmadamente venceu: **consistência de âncora**. Caso Yang Mun:
  monge fictício, 2,5M seguidores em ~3 meses, 400M+ views, curso de
  US$ 50/mês (ChatGPT + Nano Banana + ElevenLabs). Valida os ensaios
  ilustrados dos pregadores (§8c).
- **O nosso cruzamento está VAZIO em EN e PT-BR**: ninguém faz sermão
  histórico real + banco de micro-clipes IA próprio + estética sóbria. Os
  canais de Spurgeon existentes usam imagem estática; os cristãos de IA que
  bombam são espetáculo épico (The AI Bible) ou humor Veo 3 (Vlog Bíblico,
  46M views TikTok).
- ⚠️ Precedente de risco: The Power of the Word (800k) desmonetizado em 2026
  por "inauthentic content". Defesa nossa: texto real de domínio público,
  curadoria editorial (mine_clips), rotação de famílias, IA declarada.

### 10e. O plano de qualidade (aguardando ok do Gabriel)

**Calibração por ~US$ 3, três vias com os MESMOS 5 stills:**
1. 5B dentro da spec (1280x704, 121f, 50 steps): mede quanto era config.
2. **14B fp8 + Lightning** na RunPod com a receita do §10b (o candidato a
   cavalo de trabalho, ~US$ 0,01-0,03/clipe).
3. Kling 2.5 TP + Hailuo 02 via fal.ai (o teto de qualidade, US$ 0,27-0,35).
   ⚠️ Gate: conta fal.ai + ~US$ 5 (credencial + dinheiro do Gabriel).

Gabriel escolhe no olho → volume no vencedor (US$ 3-10 local ou US$ 81-105
API) → pós em lote (RIFE + grain + LUT) → biblioteca no R2.

Canais pra acompanhar (nossos "professores"): Next Diffusion (loops FLF2V,
tutorial escrito público), CaoCao2025 (settings na descrição), AI2Play
(loops no Kling, exemplos do nosso nicho: lareira, templo), Olivio Sarikas,
MDMZ, Curious Refuge, Tao Prompts (Hailuo), Preguiça Artificial (BR).

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
