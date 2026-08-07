# Setup e armadilhas do ambiente

## O contrato da composição hyperframes (NÃO invente flags)

A CLI é um renderizador de composições HTML/GSAP. Ela **não** tem `--transparent`,
`--width`, `--height` nem `--duration`. Tudo isso vem do HTML. Escrito de memória, o modelo
alucina essas flags e um `window.timeline` que não existe — e queima um ciclo de debug.

O contrato real, mínimo:

```html
<div id="root" data-composition-id="main" data-start="0" data-duration="43.87"
     data-width="1080" data-height="1350">
  <div class="cap" data-start="1.2" data-duration="1.6" data-track-index="1">…</div>
</div>
<script>
  window.__timelines = window.__timelines || {};
  const tl = gsap.timeline({paused:true});          // PAUSADA: o render dá seek nela
  tl.to("#g0w1",{scale:1.08,duration:.09}, 1.35);   // tempos ABSOLUTOS, em segundos
  window.__timelines["main"] = tl;                  // a chave = o data-composition-id
</script>
```

- Dimensões e duração: `data-width` / `data-height` / `data-duration` no root.
- Transparência: `background:transparent` no `body` + `--format webm` (ou `mov`).
- Todo elemento temporizado precisa de `data-start`, `data-duration`, `data-track-index`.
- A timeline **tem que estar pausada** e registrada em `window.__timelines[<composition-id>]`.

Render: `npx hyperframes render . --format webm -f <fps> -o cap.webm`
(o `-f` deve casar com o fps do vídeo, senão a legenda dessincroniza ao longo do clipe).

## Dependências

| O quê | Como | Nota |
|---|---|---|
| `ffmpeg` / `ffprobe` | sistema | veja as limitações abaixo |
| `opencv` | `uv add opencv-python-headless` | OpenCV **5.x removeu `CascadeClassifier`** do wheel headless; use `cv2.FaceDetectorYN` (é melhor: devolve landmarks dos olhos) |
| `hyperframes` | `npx hyperframes` | não precisa de checkout do repo |
| Anton | `assets/Anton-Regular.ttf` | embutido (SIL OFL) |
| YuNet | `assets/yunet.onnx` | embutido (OpenCV Zoo) |

## Armadilhas do ffmpeg local (macOS/Homebrew deste workspace)

- **Sem `drawtext`.** Não tente rotular frames de QC com texto — use `drawbox` e monte a
  legenda do contact sheet fora do ffmpeg (ou no nome do arquivo).
- **A ordem do `-c:v` importa.** Um codec declarado ANTES de um `-i` é o **decoder** daquele
  input. Para decodificar o WebM com alpha:

  ```bash
  ffmpeg -i video.mp4 -c:v libvpx-vp9 -i cap.webm ...   # CERTO: decoder do 2º input
  ffmpeg -i video.mp4 -i cap.webm -c:v libvpx-vp9 ...   # ERRADO: vira encoder de saída
  ```
  Colocar `libx264` no lugar errado produz **`Decoder not found`** — que parece falta de
  suporte a VP9, mas é só argumento fora de ordem. O VP9 está presente; confira com
  `ffmpeg -decoders | grep vp9` antes de acusar o ffmpeg.
- **`ffprobe -of csv=p=0:s=x` pode emitir um separador sobrando** (`1080x1080x`). Sempre pegue
  os dois primeiros campos, nunca desempacote a lista inteira.

## Por que NÃO usar as scripts da skill `embedded-captions`

Ela resolve outro problema (legenda cinematográfica com a palavra ATRÁS do sujeito) e as
scripts dela exigem duas coisas que aqui não existem/não valem a pena:

1. um **checkout do hyperframes** (`packages/cli/dist/cli.js`) — só temos o CLI via `npx`;
2. um **matte** do sujeito (~15 min de CPU por vídeo) — necessário só pra oclusão. Legenda de
   rail fica **na frente** do sujeito e não precisa de matte nenhum.

Se um dia a legenda tiver que passar atrás da pessoa, aí sim é `embedded-captions`.

## Custo

Render da camada de legenda ≈ **1× tempo real** (44s de vídeo → ~44s). Um lote de 10 min de
material leva ~10-12 min. O Bash tem teto de 10 min por chamada — rode o lote em background.
