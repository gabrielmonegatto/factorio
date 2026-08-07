---
name: recriar-reel
description: >
  Traduz ou recria do zero um Reels baixado (formato "análise de viral" com narração,
  clipes de terceiros e legendas cinéticas): redublagem com voz ElevenLabs, cobertura
  de todos os textos do editor, trilha tratada sem ficar "oca", legendas palavra-a-palavra
  sincronizadas e design próprio em preto-roxo. Entrega mp4 720x1280 pronto em ~/Downloads.
  TRIGGER quando o usuário disser "baixei um vídeo/reels, quero ele em espanhol",
  "refaz esse vídeo em espanhol", "recria esse vídeo do zero", "modela ele do zero",
  "traduz esse reels", ou apontar um reel de outro criador para virar versão dele.
  NÃO usar para editar gravação própria de talking-head (use talking-head-recut ou
  video-use) nem para criar vídeo sem vídeo-fonte (use faceless-explainer).
---

# recriar-reel

Recebe um Reels baixado (720x1280, tipicamente EN) e produz a versão do Pedro em outro
idioma (default: espanhol LatAm neutro), em um de dois modos:
- **Modo A — tradução por cima**: mantém o vídeo original, cobre os textos do editor,
  redubla e regera as legendas.
- **Modo B — recriação do zero**: extrai os clipes virais, reconstrói todo o design no
  template preto-roxo da marca. É o modo padrão quando o Pedro diz "do zero"/"modela".

## Regras duras (se só uma parte for lida, que seja esta)

1. **NUNCA deixe texto do editor original visível** (contadores, títulos, karaokê, CTA)
   — ghost de 0.2s já reprova. Conteúdo original embutido (labels dentro dos clipes,
   UI de app, props físicos) PERMANECE no idioma original: é a prova social.
2. **Legenda sai NO frame do corte de cena, nunca dentro do take seguinte.** Meça o
   corte real frame a frame (o scene detect erra em transições graduais).
3. **Música nunca fica "oca"**: o instrumental do demucs sozinho reprova. Áudio original
   intacto onde não há narração; sob a VO, trilha similar gerada (ou hook re-somado).
   Receita em `references/pipeline-tecnico.md` §Música.
4. **Tipografia é Poppins nas medidas nativas** (grandes 86–96 BoldItalic, apoio 46–50
   Regular, karaokê ExtraBold 54 com stroke escuro 3px). Arial reprova. Lockups são
   cascatas compactas ancoradas à esquerda — nunca palavras soltas com âncora central.
5. **QC sempre na timeline INTEIRA** (frames 1fps do resultado), nunca só na região
   editada. Falso positivo comum: glifo "corrompido" em thumb 280px — confirme em
   full-res antes de corrigir.
6. **ffmpeg**: um `-i` por uso (nunca `split` compartilhado entre segmentos de concat),
   cada segmento fecha com `trim=end_frame=K,setpts=PTS-STARTPTS,settb=1/30,setpts=N`
   e os K somam o total exato. O ffmpeg local não tem drawtext: texto = PNG via Pillow.
7. **Medidas sempre em crop nativo 720x1280**, nunca em thumbnail escalada.

## Workflow

1. **Entender o vídeo**: `ffprobe` (fps/duração) + cortes de cena
   (`select='gt(scene,0.25)',showinfo`) + transcrição word-level
   (`uv run python helpers/transcribe.py <video> --language en` no repo video-use)
   + storyboard por agente lendo frames 1fps (texto do editor vs conteúdo original,
   posições, janelas). Output: mapa de seções com timestamps.
2. **Roteiro**: traduza por FRASE, cada frase presa à janela da sua cena (naturalidade
   > literalidade; encurte ~15% — a voz grave é lenta). CTA vira palavra-chave local
   ("Proven"→"Aprobado", "Formats"→"Formatos").
3. **Locução**: ElevenLabs `/with-timestamps`, voz Alejandro Durán
   (`sKgg4MPUDBy69X7iv3fA`), 1 request por segmento, `atempo` ≤1.18 para caber na
   janela; overflow >0.15s = encurtar o texto. Script-modelo: `scripts/gen_tts.py`.
4. **Assets de vídeo**: extraia cada clipe/região com delogo nos textos do editor.
   Armadilhas de crop em `references/pipeline-tecnico.md` §Extração (karaokê baked
   dentro de cards, cards que animam na entrada).
5. **Música**: monte o bed conforme §Música (original nas janelas limpas + trilha
   similar nivelada sob a VO). Script-modelo: `scripts/build_bed.py`.
6. **Design**: monte o overlay PNG 30fps via Pillow seguindo
   `references/design-system.md` (bg, cards, pills, badges, CTA, tipografia, cascatas
   via `line_positions`). Script-modelo: `scripts/build_overlays.py`.
7. **Render**: concat por seções com frame caps exatos + overlay único + amix da VO.
   Script-modelo: `scripts/render.sh`. Confira `nb_read_frames` = total esperado.
8. **QC**: frames 1fps do resultado inteiro → verificação (multi-agente se disponível,
   senão leitura própria por seção) + transcreva o output (Scribe, idioma alvo) para
   validar posicionamento da VO. Corrija e re-renderize até zero findings.
9. **Entrega**: copie para `~/Downloads/<nome-claro>.mp4` e reporte o que foi feito
   com timestamps verificados.

## Graus de liberdade

- **Fixo**: pipeline acima, protocolo de QC, guardrails de ffmpeg, specs de tipografia,
  voz default, "conteúdo original permanece", entrega em ~/Downloads.
- **Livre**: adaptação criativa da tradução, paleta/acentos (default preto-roxo+lilás;
  o Pedro pode pedir outra), brief da trilha gerada (desde que match de vibe medido),
  micro-layout quando o vídeo-fonte divergir do formato padrão.

## Ponteiros

- `references/pipeline-tecnico.md` — leia ANTES dos passos 4, 5 e 7 (extração, música,
  ffmpeg, QC: todas as armadilhas conhecidas com o porquê).
- `references/design-system.md` — leia ANTES do passo 6 (paleta, medidas, tipografia).
- `references/exemplos.md` — pares certo/errado reais; leia se for a primeira execução.
- `scripts/` — implementações de referência funcionais (adapte, não reescreva do zero).
- `assets/fonts/` — família Poppins pronta (não dependa de download).
