# Palmier Pro via MCP — playbook real (produção "Anuncio Narrativa ES", jul/2026)

Servidor HTTP local `http://127.0.0.1:19789/mcp` (MCP streamable, respostas SSE).
Timing: TIMELINE em frames, SOURCE em segundos. IDs são prefixos curtos — devolver
exatamente como vieram.

## Chamadas que funcionam (schemas conferidos na prática)

- `new_project {name, fps, aspectRatio:"9:16", quality:"720p"}`
- `import_media {source:{path}|{matte:{hex,aspectRatio:"Project"}}, name, folder}`
  → `{mediaRef, status}`; cópia roda em background → polle `get_media
  {pending:true}` até vazio.
- `add_clips {entries:[{mediaRef, startFrame, endFrame, trackIndex?}]}`
  - Campo é **entries** (não "clips"); **trackIndex** (não "track").
  - `trackIndex` para track inexistente → erro "out of range (0..-1)"; OMITA
    e a track é criada (video → V1, V2...; audio → A1...).
  - Áudio: `endFrame - startFrame` ≤ frames do source (não estica).
  - Mesmo span + mesma track = SUBSTITUI o clipe existente (`removedClipIds`).
  - Clipes de vídeo com áudio embutido criam track A extra com o lado-áudio
    "folded" — remover essa track remove os lados-áudio juntos (ok).
- `manage_tracks {set:[{index, muted?, hidden?, syncLocked?}], reorder:[{index,to}],
  remove:[index]}` — NÃO existe criação; índices mudam após qualquer operação
  ("Track indices shifted — re-read").
- `add_captions {language:"es", maxWords, textCase:"upper", fontName, fontSize,
  isBold, color, highlightColor, borderColor, animation:"wordReveal",
  alignment, transform:{centerX,centerY}}` → `{captionGroups:[{captionGroupId,
  clipCount, frameRange, shared}]}`. Transcreve o áudio DA TIMELINE inteira.
- `get_timeline {captionDetail:true}` → clips de caption como linhas
  `[clipId, startFrame, endFrame, text]` — **JANELADO** (~200 por leitura):
  loop ler→remover até nada fora do critério.
- `remove_clips {clipIds:[...]}` — lotes de ~60 ok.
- `update_text {captionGroupId | clipIds, color, highlightColor, fontSize,
  fontName, animation, content, transform}` — restyle de grupo inteiro ou de
  clips específicos (refino por atos).
- `export_project {outputPath}` → H.264, renderiza em background
  ("A system notification will report completion").

## Erros vividos e a recuperação

1. **"transport dropped mid-call" em import de diretório** → o import PODE ter
   aterrissado. `get_media` antes de repetir. Na produção: 2 drops = os 82
   clipes importados 1x cada (sem duplicar por sorte de timing — SEMPRE conferir).
2. **Servidor mudo por minutos** após imports pesados (scan/cópia síncrona).
   Probe em background: `until curl -s --max-time 5 -X POST .../mcp -d
   '<initialize>' | grep -q 200; do sleep 5; done`. Não reiniciar o app à toa —
   ele volta sozinho.
3. **Tools MCP nativos caem** quando o app reinicia (o harness desconecta).
   O client `scripts/palmier.py` segura a sessão própria (arquivo
   `.palmier_session`) e faz streaming do SSE até chegar o id da resposta
   (ler até EOF trava: o servidor mantém o stream aberto).
4. **fontName com fonte não instalada** falha silencioso → `cp fonte.ttf
   ~/Library/Fonts/` antes.
5. **Filtro de captions**: manter clip se overlap com alguma janela de texto
   ≥ 35% da duração do clip. Produção: 309 criados → 176 removidos → ~133
   dentro das janelas do modelo (3 rounds de leitura janelada).

## Receita de swap (lettering/áudio/clipe localizado)

1. Renderizar/gerar o asset novo → `import_media` → poll pending.
2. `get_timeline` para achar o índice ATUAL da track alvo (labels são estáveis,
   índices não).
3. `add_clips` no MESMO span/trackIndex → substitui.
4. `export_project` de novo (não é incremental — re-renderiza tudo).

## Estrutura de tracks da produção-referência

V3 captions nativas filtradas (topo) · V2 lettering ProRes (hidden, reserva) ·
V1 128 cortes b-roll/mattes (muted) · A1 áudio final (VO+trilha).
