# Specs técnicas — video lettering (720x1280 @30fps)

## Tipografia (medida do vídeo-modelo em resolução nativa)

- Fonte: **Anton** (assets/fonts/Anton-Regular.ttf), caps.
- Corpo: telas normais 76px (fit até 620px de largura, reduzindo de 4 em 4);
  punch words 150px; linhas empilhadas centradas, gap 18px, leading 1.12.
- Paleta: branco `(255,255,255)`; ciano `(20,190,240)`; vermelho `(240,18,16)`;
  rosa `(243,23,161)`; amarelo pontual `(250,210,80)`.
- Entrada da palavra: ramp de luminância 180ms (30%→100% da cor) NO timestamp
  falado. Saída: corte seco no fim do beat.
- Glow: só nas palavras coloridas — cópia do texto com blur gaussiano 7,
  alpha ~110, por baixo do texto nítido.
- Texto sobre b-roll: sombra dura offset (3,3) preta alpha 200 (sem tarja).
- Seta de scroll: duplo chevron branco, w=76px, y≈1120, alpha
  0.55+0.45·sin(2πt).
- Anotação nos beats: `PALAVRA OUTRA(cor) / SEGUNDA LINHA(cor)` — "/" separa
  linhas, "(cor)" colore o chunk anterior, "→" separa estados sequenciais no
  mesmo beat. O parser é depth-aware: barras e travessões DENTRO de parênteses
  não quebram nada (bug já pago).

## Prompts de b-roll (Kling via Higgsfield)

- Modelo: `kling3_0_turbo`, `aspect_ratio: "9:16"`, `duration: 5` (10 para
  beats >5s). Custo ref.: 7.5 créditos/5s.
- Estrutura do prompt (60-110 palavras, EN): estilo/gênero da imagem → sujeito
  e ação → enquadramento → luz → paleta → movimento (elementos OU câmera:
  "slow push-in"/"slow lateral pan"/"locked camera, subtle ambient motion") →
  `No text, no captions, no watermarks.` → style tail:
  `Vertical 9:16, cinematic dark ad aesthetic, heavy film grain, deep
  shadows, photorealistic.`
- Personagem-símbolo: repetir a MESMA descrição verbatim em toda cena dele.
- Submissão: ondas de ~8 em paralelo; passar `declined_preset_id` (de um
  notice anterior) em TODA chamada para pular avisos de preset; registrar
  idx→job_id num jobs.json a cada onda.
- Coleta: `show_generations(type:"video", size:100)` traz todas as URLs de uma
  vez (vai para arquivo; extrair com python). Baixar em lotes de 8 com curl.
- Ícones/motion-graphics 2D simples: renderizar local com Pillow
  (ver `scripts/make_icon_106.py`), não gastar geração.

## Áudio

- VO: ElevenLabs `/with-timestamps`, 1 request por frase, `previous_text`/
  `next_text` para prosódia; word timestamps derivados dos characters.
  Voz: grave/autoridade (ES: Alejandro Durán `sKgg4MPUDBy69X7iv3fA`;
  PT: buscar shared-voices `language=pt` por uso e validar com o Pedro).
- Beats travam nos tempos REAIS da fala (gerar VO ANTES de fechar beats.json).
- Trilha: ElevenLabs Music (`/v1/music`, `music_length_ms`), brief tipo
  "very dark muffled phonk, heavy sub bass, hypnotic, no drops, instrumental";
  escolher entre 2-3 candidatas por métrica (centroide espectral baixo ~400-800Hz,
  steadiness alto). Nivelar: rms ≈ 0.07 sob a VO (piso 0.065), fade-out 0.5s.
- Mix: `amix normalize=0` + `alimiter=0.97`; VO 1.0, trilha nivelada no bed.

## Montagem (scripts/montage.py)

- 1 segmento por beat, `-c:v libx264 -crf 18`, cap exato
  `trim=end_frame=K,setpts=PTS-STARTPTS` (os K somam o total do vídeo).
- Clipe menor que o beat: ping-pong (concat normal+reverse) e trim.
- Beat de texto com fundo não-preto (ex.: cartela creme da oferta): trocar a
  cor do lavfi por beat (`color=0xEFE8DC`).
- Concat por demuxer de arquivos (`-f concat -c copy`) → passe final único:
  overlay do type PNG seq + `vignette=PI/5` + áudio.
- NUNCA compartilhar split entre segmentos; ffmpeg 8: overlay não termina no
  EOF do main — o cap de frames é a blindagem.

## QC obrigatório

1. `nb_read_frames` == frames esperados.
2. Frames 1fps do vídeo INTEIRO revisados (multi-agente quando disponível).
3. Brilho médio por segundo vs esperado: beat de b-roll com luminância <8
   E descrição clara = buraco (mas cenas dark legítimas existem — conferir o
   frame antes de "corrigir").
4. Transcrever o output e conferir frases nas janelas.
5. Trabalhar SEMPRE em disco persistente (repo), nunca no scratchpad de /tmp.

## REGRA DE OURO da dublagem (lição paga 2x)

Legendas/karaokê sincronizam com a transcrição Scribe DO ÁUDIO DUBLADO FINAL
(idioma alvo), nunca com timestamps derivados do TTS nem com os tempos do idioma
original. Fluxo: gerar VO -> mixar -> transcrever o mix (`--language es`) ->
casar palavras com janela LARGA (t0-1.2 a t1+2.0, lookahead 14 palavras) ->
só então renderizar o lettering.
