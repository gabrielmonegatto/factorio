---
name: edit-video-lettering
description: >
  Monta e edita um vídeo de tipografia cinética (video lettering) dentro do
  Palmier Pro via MCP: cria o projeto 9:16, importa b-rolls/mattes/áudio,
  posiciona os cortes frame a frame pelos beats, aplica as legendas (captions
  nativas com karaokê OU camada ProRes com alpha), filtra legendas para as
  janelas do vídeo-modelo e exporta. TRIGGER quando o usuário disser "monta no
  palmier", "edita pelo palmier pro", "recria esse vídeo pelo palmier",
  "coloca como captions no palmier", ou pedir a edição/versão de um video
  lettering dentro do Palmier. NÃO usar para GERAR os assets do formato
  (roteiro→VO/b-rolls/lettering) — para isso use video-lettering; nem para
  traduzir reel com vídeo-modelo — use recriar-reel.
---

# edit-video-lettering

Recebe os assets de um video lettering (b-rolls, áudio final, storyboard de
beats e, opcionalmente, a camada de lettering renderizada) e entrega o vídeo
montado e exportado pelo Palmier Pro — com a timeline editável no app.

## Regras duras

1. **Beats → frames exatos.** Todo clipe entra com startFrame/endFrame
   pré-computados do storyboard (fps do projeto; nunca multiplicar por fps na
   mão — os tools convertem source↔timeline). Os frames somam a duração exata.
2. **Legenda só onde o modelo tem legenda.** Captions nativas nascem no vídeo
   INTEIRO (add_captions transcreve tudo); filtre removendo clips com overlap
   <35% com as janelas de texto do storyboard. `captionDetail:true` é
   JANELADO (~200 linhas) — repita ler+remover até voltar limpo.
3. **Áudio dos b-rolls gerados: sempre mutar** (`manage_tracks set muted`) —
   clipes Kling trazem áudio-fantasma que vaza no mix.
4. **Swap por sobreposição**: adicionar um clipe no MESMO span/track substitui
   o antigo (vem `removedClipIds`) — é o idioma para trocar lettering, áudio
   ou clipes localizados. Nunca precisa remover antes.
5. **Transport dropped ≠ falhou.** Import de diretório pode derrubar a conexão
   e MESMO ASSIM aterrissar no app — confira `get_media` antes de reimportar
   (senão duplica tudo). Servidor pode ficar mudo minutos após imports
   pesados: espere com probe `until curl` em background, não desista.
6. **Fonte custom**: instale o .ttf em `~/Library/Fonts` ANTES do
   add_captions/add_texts (Palmier usa fontes do sistema).
7. **Export renderiza em background**: vigie o arquivo estabilizar (tamanho
   igual em 2 leituras) antes de reportar pronto; depois QC de frames.

## Workflow

1. **Conexão** — servidor local: `claude mcp add --transport http palmier-pro
   http://127.0.0.1:19789/mcp` (no diretório-projeto certo!). Se os tools MCP
   caírem no meio (restart do app), use `scripts/palmier.py` (client HTTP
   JSON-RPC/SSE): `python3 palmier.py tools|schema <tool>|call <tool> '<json>'`.
2. **Projeto** — `new_project` (nome, fps 30, 9:16, 720p). `get_projects` /
   `open_project` se já existir.
3. **Imports** — arquivos individuais (retornam rápido, cópia em background;
   polle `get_media pending:true` até esvaziar). Mattes de cor:
   `import_media {source:{matte:{hex,aspectRatio:"Project"}}}` para os fundos
   das cartelas (preto, creme da oferta). Diretórios: funcionam mas seguem a
   regra 5.
4. **Montagem** — `add_clips {entries:[{mediaRef,startFrame,endFrame,
   trackIndex}]}` (campo é `entries`; tracks se AUTOCRIAM quando trackIndex é
   omitido; áudio: endFrame ≤ frames do source). Ordem: b-rolls+mattes numa
   track; lettering ProRes 4444 (com alpha) na track de cima; áudio final na
   track de áudio. Depois `manage_tracks` (só remove/reorder/set — não existe
   "add") para mutar/ocultar; índices MUDAM após operações — releia.
5. **Legendas** — dois caminhos (pergunte ao usuário se ambíguo):
   a. **Captions nativas** (editáveis no app): `add_captions {language,
      maxWords:4, textCase:"upper", fontName, fontSize, isBold, color,
      highlightColor, borderColor, animation:"wordReveal", transform}` —
      wordReveal+highlightColor = karaokê. Depois FILTRE (regra 2) e refine
      por atos com `update_text {captionGroupId|clipIds, ...}` (highlight
      vermelho na dor, rosa na oferta, fontSize maior em punch words).
   b. **Camada ProRes** (design completo: cores por palavra, punch words,
      degraus, seta): PNG seq → `prores_ks -profile:v 4444 -pix_fmt
      yuva444p10le` → import → clip full-span na track do topo.
   Pode manter as duas: uma track oculta (`hidden:true`) como reserva.
6. **Export** — `export_project {outputPath}` (H.264 default; omita
   outputPath → ~/Downloads). Vigie estabilizar; QC frames nos pontos-chave.

## Graus de liberdade

- **Fixo**: regras acima, ordem de tracks (lettering no topo), verificação
  pós-transport-drop, filtro de captions pelas janelas do modelo.
- **Livre**: captions nativas vs ProRes vs híbrido, estilo das captions,
  quantas tracks de reserva, nome/destino do export.

## Ponteiros

- `references/palmier-playbook.md` — API real (schemas certos, erros vividos
  e como recuperar). Leia ANTES do passo 3.
- `scripts/palmier.py` — client HTTP standalone (sessão, SSE streaming).
- Assets do formato: skill **video-lettering** (geração) e **recriar-reel**
  (tradução de modelo). O storyboard/text_events deles são a fonte das
  janelas de legenda daqui.
