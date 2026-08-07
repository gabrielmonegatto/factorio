# Entrevista — reel-legenda-enquadramento (2026-07-14)

Entrevista curta: a matéria-prima foi a produção real dos 9 reels da Juliana Guerra, feita
na mesma sessão. Os blocos 3 (barra de qualidade) e 4 (modos de falha) não foram perguntados
— foram **vividos**, e por isso os pares de `exemplos.md` são todos bugs reais, não inventados.

## Bloco 1 — O job
Talking-heads já limpos entram; MP4s postáveis saem, reenquadrados no formato escolhido com o
olho no primeiro terço e legenda animada (só a fala) centrada no segundo terço. Um MP4 por
vídeo. Origem: pedido do Pedro — "ficou muito bom esses últimos vídeos com legenda com
hyperframes, queria criar uma skill dessa edição".

## Bloco 2 — Gatilho
"põe legenda animada nesses vídeos", "legenda com hyperframes", "legenda estilo reels",
"reenquadra e legenda", "deixa o olho no primeiro terço", "coloca no formato 4:5 com legenda".
**Near-miss crítico:** `enquadramento-short` (16:9→9:16 seguindo o falante, pipeline do
Cortador) compartilha "reenquadra"/"crop"/"vertical". Sem o bloco `NÃO usar para`, as duas
brigam. Também vizinhas: `embedded-captions` (palavra ATRÁS do sujeito), `video-lettering`,
`legenda-rede-social` (.srt).

## Blocos 3 e 4 — Barra e modos de falha (vindos da produção real)
O que faz ser excelente: o olho **cravado** na linha (não "quase"), a legenda **centrada** na
linha em card de 1 e de 2 linhas, e só fala na tela.
Erros reais que aconteceram e viraram regra dura:
1. GSAP sobrescreve `transform` → legenda com o topo (não o centro) na linha.
2. Clipe `height:0` → legenda some do render inteiro, sem erro.
3. Reveal palavra-a-palavra → invisíveis ocupam espaço → legenda descentraliza.
4. Token `type="audio_event"` do Scribe → `(MÚSICA DE ENCERRAMENTO)` foi ao ar na legenda.
5. Corte que satura sem alcançar a linha → 1 vídeo em 9 fora do padrão (exigiu zoom 1,06×).
6. Constante cravada do 3:4 → quebraria em silêncio nos outros 4 formatos.
**Inaceitável:** legenda com texto que não foi falado; vídeo entregue sem conferir as linhas
desenhadas (os dois bugs de geometria passaram por revisão de código e só apareceram na imagem).

## Decisões (AskUserQuestion, 2026-07-14)
- **Formatos:** 9:16, 4:5, 3:4, 1:1, 16:9 — a skill PERGUNTA antes de rodar.
- **Escopo:** só reframe + legenda. Corte de erros continua etapa separada.
- **Estilo:** Anton / branco+borda preta / ouro `#FFC72C` fixo, com override sob pedido.
- **Nome:** `reel-legenda-enquadramento`.

## Bloco 6 — Graus de liberdade
Fixo: olho em `H/3`, legenda em `2H/3`, só fala, card inteiro (karaokê), vídeo fora do Chrome,
QC com linhas desenhadas. Livre: escolha semântica das palavras de ênfase, tamanho do card
(2-5 palavras), fonte/cores sob override.

## Bloco 7 — Execução
ffmpeg + opencv (`FaceDetectorYN`; OpenCV 5 removeu `CascadeClassifier`) + `npx hyperframes`.
Assets embutidos: Anton (SIL OFL) e yunet.onnx. Sem checkout do hyperframes, sem matte.
Pipeline: (corte de erros, separado) → ESTA SKILL → publicação.
