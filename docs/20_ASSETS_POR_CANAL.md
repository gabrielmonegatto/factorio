# 🎬 ASSETS POR CANAL — a lista completa pra um vídeo ficar pronto

> Levantada em 20/08/2026 **do vídeo real que está no ar**, lendo o que o
> `build_job.py` baixa e inventariando o R2 do Spurgeon. Não é de memória.
> Serve de checklist pra qualquer canal novo do arquétipo TREASURES.

---

## Como ler esta lista

Os assets se dividem em **três naturezas**, e a diferença muda tudo no esforço:

| Natureza | Quanto precisa | Por quê |
|---|---|---|
| **Por vídeo** | 1 de cada, N vezes | muda a cada sermão; a máquina gera |
| **Rotativo** | um punhado, reusado em ciclo | fórmula determinística `(N-1) % total` escolhe |
| **Fixo do canal** | 1 de cada, pra sempre | identidade; feito uma vez |

O rotativo é o que evita o canal parecer o mesmo vídeo 100 vezes, sem exigir
100 imagens. Com 26 fundos, o vídeo 27 repete o fundo do vídeo 1: ninguém nota.

---

## 1. POR VÍDEO (a máquina gera, 1 de cada por sermão)

| # | Asset | Formato | Quem produz | Estado no Moody |
|---|---|---|---|---|
| 1 | **Texto do sermão** | `.txt`/md limpo | mineração (CCEL/Gutenberg) | ⬜ minerar 13 obras |
| 2 | **Copy de marketing** (título, thumbnailText ≤6 palavras, descrição) | `marketing_meta.json` | LLM-função | ⬜ generalizar prompt |
| 3 | **Narração do sermão** | `sermon_NNNN.wav/mp3` | Kokoro (`am_adam` 0.84) | ⬜ |
| 4 | **Transcrição do sermão** | `transcript.json` word-level | AssemblyAI/Groq | ⬜ |
| 5 | **Narração do hook** | `hook.wav` | Kokoro | ⬜ |
| 6 | **Transcrição do hook** | `hook.json` | AssemblyAI/Groq | ⬜ |
| 7 | **Narração do CTA final** | `cta_narration.wav` | Kokoro | ⬜ |
| 8 | **Transcrição do CTA** | `cta_narration.json` | AssemblyAI/Groq | ⬜ |
| 9 | **Thumbnail** | `.png` | Remotion (`still Thumbnail`) | ✅ sai do template |
| 10 | **Legenda** | queimada no vídeo | derivada de 4/6/8 | ✅ automática |

**Legenda não é asset separado:** ela nasce do timestamp por palavra das
transcrições. Por isso 4, 6 e 8 existem: sem transcrição não há legenda sincronizada.

---

## 2. ROTATIVOS (o Spurgeon hoje, como referência de quantidade)

| Asset | Spurgeon tem | Mínimo aceitável | Recomendado |
|---|---|---|---|
| **Fundo de época** (`cathedral/`) | **26** | 8 | **15 a 25** |
| **Retrato/busto do pregador** (`avatars/`) | **5** variações + 1 base | 3 | **5** |
| **Trilha de fundo** (global, `_globalassets/worship/`) | **4** (3 worship + 1 de 432 Hz) | 3 | 4 a 6 |

**A trilha é GLOBAL, não por canal.** Vive em
`channels/channels_youtube/_globalassets/worship/` e serve todos os canais.
Não precisa gerar de novo pro Moody. ⚠️ Mas ver o alerta de licença no §5.

---

## 3. FIXOS DO CANAL (uma vez, pra sempre)

| Asset | Arquivo | O que é |
|---|---|---|
| **Avatar do canal** | `_assets/channelavatar.png` | foto de perfil, aparece no card de inscrição |
| **QR code** | `_assets/qrcodes/corner_qr.png` | aponta pro `/go/<canal>` — **um por canal** |
| **CTA de abertura narrado** | `_assets/introfixed.mp3` | "link na descrição"; mesma voz do canal |
| **CTA de fechamento narrado** | `_assets/finalfixed.mp3` | pedido de inscrição |
| **Vídeo de intro** | `_assets/pre_rendered/intro_cta_fixed.mp4` | pré-renderizado, economiza render |
| **Vídeo de outro** | `_assets/pre_rendered/outro_cta_fixed.mp4` | idem |
| **Endscreen** | `_assets/pre_rendered/endscreen_fixed.mp4` | tela final |
| **Banner do canal** | (no YouTube, não no R2) | arte de capa |

🧨 **MINA dos CTAs:** `introfixed.mp3` e `finalfixed.mp3` são **assets mutáveis
embutidos no vídeo**. Trocar um deles torna VELHO todo render feito antes, e o
gate de frescor dispara re-render de tudo. Já queimou um dia de trabalho em
29/07: a versão velha ficou cacheada no volume e o gate dizia "fresco" com
conteúdo velho. Por isso o download deles é `force=True`.

---

## 4. A CONTA FECHADA PRO MOODY

O que tu precisa produzir pra o canal existir:

### Imagens (Workers AI ou banco próprio)
- [ ] **15 a 25 fundos** de época, ambiente quente/âmbar (contraste com a catedral fria do Spurgeon)
- [ ] **5 retratos/bustos** do Moody, tratados no mesmo estilo da família
- [ ] **1 avatar** de canal
- [ ] **1 banner** de canal
- [ ] **1 QR code** apontando pra `mananciall.org/go/moody`

### Áudio fixo (Kokoro `am_adam` 0.84, mesma voz do canal)
- [ ] **1 CTA de abertura** narrado
- [ ] **1 CTA de fechamento** narrado

### Vídeo pré-renderizado (Remotion, a partir das imagens acima)
- [ ] **intro**, **outro** e **endscreen**

### Trilha
- ✅ **nada a fazer**: usa as 4 globais

**Total de peças novas: ~26 imagens, 2 áudios, 3 vídeos curtos.**
Fora isso, tudo o mais é por vídeo e a esteira gera sozinha.

---

## 5. ⚠️ Duas pendências que valem checar antes de escalar

**Procedência das 4 trilhas.** Elas são globais e vão entrar em TODOS os canais
da rede. Se alguma tiver licença duvidosa, o problema se multiplica por 10
canais em vez de ficar contido em 1. Vale confirmar a origem de cada uma antes
do segundo canal (ver `13_CANAL_MUSICA.md` sobre por que trilha é o direito
mais traiçoeiro).

**Só 4 trilhas para 10 canais.** Se todos usarem as mesmas 4, os canais soam
iguais entre si, e a regra da rede (§ doc 19) diz que derivação precisa de
transformação. Ideal: 3 a 4 trilhas **próprias por canal**, ou pelo menos um
subconjunto diferente por canal.
