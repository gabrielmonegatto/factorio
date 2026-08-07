# Pares certo/errado — todos reais desta produção (jul/2026)

## Erro 1: tipografia por chute

❌ **Errado:** lockups em Arial Bold Italic, grandes 72–84px e apoio 34px, medidos
"de olho" em thumbnails.
✅ **Certo:** medir o original em crop nativo 720x1280 → Poppins BoldItalic 86–96px,
apoio Poppins Regular 46–50px, karaokê ExtraBold 54 com stroke 3px.
**Por quê:** o Pedro reprovou DUAS vezes ("ficou estranho", "tá uma merda") até a
fonte e a escala baterem. Fonte errada não se conserta com posição.

## Erro 2: palavras soltas com âncora central

❌ **Errado:** desenhar cada palavra do título com anchor central em posições chutadas
→ "fue⠀⠀⠀un" com espaço duplo, "de" flutuando longe da frase.
✅ **Certo:** cascata left-baseline: linhas com baseline compartilhada, x acumulado
por largura de prefixo, escada compacta (gaps 43–67px).
**Por quê:** o formato é um lockup diagramado, não palavras espalhadas.

## Erro 3: música "resolvida" sem ouvir como música

❌ **Errado (1ª tentativa):** instrumental do demucs sob a VO → música "oca" (hook
vocal arrancado). ❌ **Errado (2ª tentativa):** detectar que a track é loop e ladrilhar
o INTRO no vídeo inteiro → "não é a música que tocava atrás da voz".
✅ **Certo:** original intacto nas janelas sem narração + (hook re-somado no
instrumental do timeline real OU trilha similar gerada e nivelada por métrica).
**Por quê:** a música evolui; o ouvido do Pedro pega tanto o buraco quanto a troca.

## Erro 4: legenda invadindo o take seguinte

❌ **Errado:** deixar a frase "Esto fue un patrón viral" na tela até o áudio acabar
(8.3s) sendo que o corte é em 7.567s.
✅ **Certo:** olhar frame a frame o corte real e clampar a legenda para sair NO corte;
revelar as palavras mais rápido que a fala para a frase completar antes.
**Por quê:** legenda atravessando corte é o erro que o espectador (e o Pedro) vê na hora.

## Erro 5: concat de ffmpeg confiado sem prova

❌ **Errado:** `split` do bg compartilhado entre seções; segmentos sem cap de frames
→ vídeo congela no meio e o QC "passou" porque só olhamos a região editada.
✅ **Certo:** 1 input por uso; todo segmento fecha com `trim=end_frame=K,...,setpts=N`;
conferir `nb_read_frames`; QC 1fps do vídeo INTEIRO após TODA re-render.
**Por quê:** o freeze aconteceu 3 vezes, e 2 passaram pelo QC míope.

## Erro 6: corrigir falso positivo sem confirmar em full-res

❌ **Errado:** auditor reporta "palavra 'hunYana' corrompida"; sair mexendo na fonte.
✅ **Certo:** crop full-res do frame → "humana" perfeita; era artefato do JPEG 280px.
**Por quê:** thumb comprimida mente sobre glifos; conserto às cegas quebra o que funciona.

## Erro 7: crop que traz lixo junto

❌ **Errado:** cropar o card do source no trecho em que ele ainda anima (vaza fundo
verde original nas bordas) e com o karaokê EN baked dentro da região.
✅ **Certo:** extrair do trecho estático ou re-cropar o clipe fullscreen; texto baked
dentro do crop = tarja escura na janela toda (não delogo em fundo claro).
**Por quê:** todo pixel do source dentro do crop vem junto — inclusive o que você
não viu no thumbnail.
