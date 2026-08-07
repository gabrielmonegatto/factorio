---
name: reel-legenda-enquadramento
description: >
  Reenquadra talking-heads para o formato pedido (9:16, 4:5, 3:4, 1:1 ou 16:9) ancorando o
  OLHO na linha do primeiro terço, e queima legenda animada karaokê (Anton, caixa alta, branca
  com borda preta, ênfase em ouro) centrada na linha do segundo terço, via hyperframes.
  Entrega MP4 pronto pra postar. TRIGGER quando o usuário pedir "põe legenda animada nesses
  vídeos", "legenda com hyperframes", "legenda estilo reels", "reenquadra e legenda",
  "deixa o olho no primeiro terço", "coloca no formato 4:5 com legenda", ou mandar uma pasta
  de talking-heads pedindo legenda.
  NÃO usar para: reenquadrar 16:9 seguindo o falante com keyframes (é enquadramento-short,
  do pipeline do Cortador); legenda cinematográfica com palavra ATRÁS do sujeito (é
  embedded-captions); tipografia cinética sem talking-head (é video-lettering); cortar erros
  de gravação (etapa anterior, separada).
---

# Reel — legenda e enquadramento

## Propósito

Pega talking-heads já limpos e entrega MP4s postáveis: reenquadrados no formato escolhido com
o olho na linha do primeiro terço, e com legenda animada (só o que foi falado) centrada na
linha do segundo terço. Um MP4 por vídeo de entrada.

## Regras duras

1. **Pergunte o formato ANTES de rodar qualquer coisa.** É a única variável do job; errar
   significa refazer tudo (detecção, corte, render). Ofereça 9:16, 4:5, 3:4, 1:1, 16:9.
2. **A geometria é FÓRMULA, nunca número.** Olho em `H/3`; centro da legenda em `2H/3`;
   corpo da fonte `0.0815 × min(W,H)` (porque a skill atende 5 formatos — qualquer constante
   cravada só funciona num deles e quebra silenciosamente nos outros).
3. **Ache o olho pela MEDIANA de ~20 frames, nunca por um frame.** A pessoa gesticula e se
   mexe; um frame isolado erra o alvo em mais de 100px.
4. **Se o corte não alcança a linha, aplique o menor zoom que alcance — não aceite "quase".**
   Talking-head filmado baixo no quadro não chega ao primeiro terço só recortando
   (caso real: olho em y=1005 num source 1080×1920, faltavam 45px; zoom 1,06× resolveu).
5. **Só vira legenda o que foi FALADO — `type == "word"`.** O Scribe emite eventos de áudio
   como tokens (`(música de encerramento)`, `(resmunga)`); se não filtrar, eles aparecem na
   tela como se fossem fala. Já vazou uma vez em produção.
6. **O card entra INTEIRO; palavra não aparece uma a uma.** Palavra ainda invisível continua
   ocupando espaço e joga o texto visível pra esquerda — a legenda descentraliza. A animação
   é karaokê: card inteiro no ar, pop na palavra ao ser falada.
7. **`.cap` carrega só `autoAlpha`; `.txt` carrega o `transform`.** O GSAP sobrescreve a
   propriedade `transform` inteira — se o posicionamento vertical depender dela
   (ex.: `translateY(-50%)`), ele é apagado e a legenda desce pra altura errada.
8. **O clipe de legenda ocupa o FRAME INTEIRO; nunca `height:0`.** O engine recorta o clipe à
   sua caixa — altura zero faz a legenda sumir inteira do render.
9. **O vídeo NUNCA passa pelo Chrome.** Renderize só a camada de legenda (WebM/VP9 com alpha)
   e componha com ffmpeg — assim a imagem não sofre um segundo reencode de geração.
10. **Ênfase escassa: ~1 a cada 5 cards.** Ouro em tudo é ouro em nada. Só números, valores e
    palavras de impacto.
11. **Card nunca termina em palavra funcional** (`de`, `que`, `o`, `pra`…) — pendurar artigo
    no fim da linha quebra a leitura no pior ponto possível.
12. **Confira com as linhas dos terços DESENHADAS antes de entregar.** Os dois bugs de
    geometria desta skill passaram por revisão de código e só apareceram na imagem.

## Workflow

0. **Pergunte o formato** (AskUserQuestion). Estilo padrão = Anton / branco / ouro `#FFC72C`;
   só pergunte estilo se o usuário mencionar querer outro.
1. **Transcrição word-level.** Reaproveite JSON do Scribe se já existir (`edit/transcripts/`);
   senão `npx hyperframes transcribe`. Se os vídeos foram cortados, use a transcrição do
   CORTADO — a do original está fora de sincronia.
2. **Reenquadre:** `python scripts/reframe.py VIDEO... --aspect <fmt> --out DIR/_reframe`
   Confira o relatório: todo vídeo deve fechar `eye_final == target`.
3. **Legenda:** `python scripts/captions.py --video DIR/_reframe/X.mp4 --transcript T.json
   --out PROJ/X` (opcional `--punch palavras.txt`, `--accent`, `--font`).
4. **Render + composição:** `bash scripts/render.sh PROJ/X DIR/_reframe/X.mp4 DIR/X.mp4`
   (~1× tempo real; rode em background e vá acompanhando).
5. **QC obrigatório** — leia `references/qc.md`. Sem os dois testes de lá, não entregue.

## Graus de liberdade

- **Fixo:** olho em `H/3`; legenda em `2H/3`; só fala vira legenda; card inteiro (karaokê);
  vídeo fora do Chrome; QC com linhas desenhadas.
- **Livre:** escolha das palavras de ênfase (semântica, não lista fixa); tamanho dos cards
  dentro de 2-5 palavras; fonte/cores se o usuário pedir override.

## Ponteiros

- `references/exemplos.md` — pares certo/errado. **Leia antes de mexer nos scripts.**
- `references/qc.md` — o protocolo de verificação. Leia antes de entregar.
- `references/setup.md` — dependências e armadilhas do ffmpeg local. Leia se algo quebrar.
- `scripts/` — `reframe.py`, `captions.py`, `render.sh`.
- `assets/` — `Anton-Regular.ttf` (SIL OFL), `yunet.onnx` (detector de face, OpenCV Zoo).
