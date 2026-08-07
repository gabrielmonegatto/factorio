# Pipeline técnico — armadilhas conhecidas (todas pagas com retrabalho real)

Ambiente: repo `/Volumes/KINGSTON/claude/tools/video-use` (venv via `uv`, `helpers/transcribe.py`,
`ELEVENLABS_API_KEY` no `.env`). ffmpeg local SEM drawtext/subtitles/zscale.

## Timing (fonte da verdade)

- Legendas cinéticas de reel seguem a fala palavra a palavra → o word-level do Scribe
  É o timing das legendas originais.
- Cortes de cena: `select='gt(scene,0.25)'` acha os cortes duros, mas ERRA transições
  graduais. Para o frame exato de um corte (onde a legenda deve sair), extraia todos
  os frames da janela (`-ss X -t Y` + `%02d.jpg`) e olhe um a um.
- A narração pode começar segundos depois do vídeo (hook sem narração) — verifique
  antes de assumir que fala = 0s. Vocais DA MÚSICA aparecem no transcript como fala.

## Locução (ElevenLabs)

- Voz por vibe: buscar `/v1/shared-voices?language=es&sort=usage_character_count_1y`.
  Grave/autoridade: Alejandro Durán `sKgg4MPUDBy69X7iv3fA` (fala ~15% mais devagar —
  encurte os textos). Comercial/rápida: Fernando Martínez `dlGxemPxFMTY7iXagmOj`.
- 1 request por frase com `/with-timestamps` (character timestamps → word timestamps).
  `previous_text`/`next_text` melhoram a prosódia. Cache por segmento (não regerar tudo).
- Encaixe: `atempo` até 1.18 é imperceptível. Overflow >0.15s sobre o próximo segmento
  = reescrever mais curto, nunca acelerar mais.

## Extração de assets (delogo/crop)

- `delogo` com `enable=between(t,a,b)` é invisível em fundo escuro/gradiente. Em fundo
  claro/texturizado vira mancha — aí use tarja escura feathered (Pillow, alpha ~250)
  no overlay, POR CIMA de onde o texto passa.
- Blur NÃO esconde texto branco (espalha em mancha clara). Caixa preta dura em gradiente
  é feia. Ordem de preferência: delogo (fundo liso) > tarja feathered (fundo vivo).
- **Karaokê baked DENTRO do crop**: se o texto do editor foi queimado sobre a região
  que você vai cropar (card, celular), ele vem junto. Cubra com tarja na janela toda
  ou extraia de outro trecho da fonte (o clipe cheio em fullscreen).
- **Cards que animam na entrada**: crop estático pega o card em movimento e vaza o
  fundo original pelas bordas. Use o trecho onde o card está parado, ou recrie a
  partir do clipe fullscreen re-cropado.
- Pill que cobre texto que SCROLLA: keyframes de y medidos frame a frame (o movimento
  nunca começa quando você acha) + pill 20% maior que o alvo.

## Música (a lição mais cara da história desta skill)

Regra: o espectador não pode sentir a música "oca" nem trocada.
1. **Janelas sem narração** → áudio ORIGINAL intacto (crossfade 0.15s nas emendas).
2. **Sob a VO** → escolha na ordem:
   a. Trilha original identificada (Shazam via `uv run --python 3.11 --with shazamio`;
      desconfie de match único — confirmar em 2 trechos) → usar a faixa real.
   b. Instrumental demucs + **hook vocal re-somado**: o stem de vocals numa janela onde
      o narrador cala = hook isolado; some-o de volta na grade do loop (período por NCC
      sample-accurate — busca em grade de ms FALHA, corr morre com ~1ms de offset).
      NUNCA ladrilhar o intro no vídeo todo: a música evolui e o Pedro percebe.
   c. **Trilha similar gerada** (ElevenLabs Music `/v1/music`, `music_length_ms`):
      brief pelo caráter MEDIDO da original (BPM por autocorrelação de onset, centroide
      espectral — "very dark muffled phonk" deu centroide 446Hz vs 834Hz da referência).
      Gere 2-3 candidatas e escolha por métrica, não por fé.
3. Nivelamento: alvo = rms da música original ×0.8~0.85, com PISO de 0.065 (fonte
   quase muda gera alvo inaudível). Fade-out 0.5s no fim. Demucs local:
   `uvx --python 3.11 --from demucs --with soundfile --with torchcodec demucs -n
   htdemucs_ft --shifts=2 --two-stems=vocals` (torchcodec obrigatório pro save).

## ffmpeg — montagem por seções (concat)

- **Um `-i` por uso.** `split` compartilhado entre segmentos do concat trava o grafo
  (freeze do último frame). Imagem de fundo usada em 5 seções = 5 inputs `-loop 1 -t X`.
- **ffmpeg 8: `overlay` NÃO termina quando o main acaba** — segue até o secundário
  acabar repetindo o main. Blindagem: TODO segmento fecha com
  `trim=end_frame=K,setpts=PTS-STARTPTS,settb=1/30,setpts=N` e os K somam o total
  exato de frames. Sem isso o PTS explode (já vimos vcat de 11min e de 37min).
- Texto/gráficos = sequência PNG RGBA 30fps única (Pillow, cache de frames idênticos
  por chave de conteúdo) + UM `overlay` final. Nunca dezenas de drawtext/overlays.
- Scroll de conteúdo: imagem alta (ex. 720x2300) + `crop=720:1280:0:'(ih-1280)*min(t/D,1)'`.
  Fundo da imagem alta = gradiente ESTICADO (resize), nunca tile (a emenda aparece).
- lavfi (`color=black`) também é 1 input por segmento.
- Áudio: `amix=inputs=N:duration=first:normalize=0` + `alimiter=limit=0.97`;
  VO com `adelay=ms|ms`; bed como primeiro input do amix.

## QC (protocolo que pega o que o olho pula)

1. `nb_read_frames` == total esperado (freeze de concat aparece aqui primeiro).
2. Frames 1fps do vídeo INTEIRO → auditoria por seção (multi-agente quando disponível)
   com spec do que DEVE estar em cada janela. QC míope (só a região editada) já deixou
   passar 2 freezes.
3. Falso positivo conhecido: glifo "corrompido" em thumb 280px q6 — confirmar em crop
   full-res antes de mexer (aconteceu 2x com a mesma palavra).
4. Transcrever o OUTPUT (Scribe, idioma alvo) e conferir cada frase na sua janela.
5. Boundaries críticos (cortes de cena, entrada/saída de legenda): frames a 100ms.

## REGRA DE OURO da dublagem (lição paga 2x)

Legendas/karaokê sincronizam com a transcrição Scribe DO ÁUDIO DUBLADO FINAL
(idioma alvo), nunca com timestamps derivados do TTS nem com os tempos do idioma
original. Fluxo: gerar VO -> mixar -> transcrever o mix (`--language es`) ->
casar palavras com janela LARGA (t0-1.2 a t1+2.0, lookahead 14 palavras) ->
só então renderizar o lettering.
