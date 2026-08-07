# QC — os dois testes obrigatórios

Os dois bugs de geometria desta skill passaram por revisão de código e só apareceram
**na imagem**. Não entregue sem rodar os dois testes abaixo.

## Teste 1 — as linhas dos terços, desenhadas

Nunca confie no relatório numérico do `reframe.py`: ele prova que o CROP está certo, não que
a legenda foi parar onde devia. Desenhe as linhas e olhe.

```bash
H=1440                       # altura do formato escolhido
T1=$((H/3)); T2=$((2*H/3))
ffmpeg -y -ss <t> -i final.mp4 -vframes 1 \
  -vf "drawbox=x=0:y=$((T1-1)):w=iw:h=3:color=red@0.9:t=fill,\
drawbox=x=0:y=$((T2-1)):w=iw:h=3:color=cyan@0.9:t=fill" check.png
```

Leia a imagem e confirme:

- a linha **vermelha** cruza os olhos da pessoa;
- a linha **ciano** passa pelo **centro** do bloco de legenda — em card de 1 E de 2 linhas
  (o bug do `transform` só aparece quando você compara os dois);
- a legenda não cobre o rosto.

Escolha os `<t>` a partir do `cards.json`, não a esmo — pegue um card de 1 linha e um de 2.

## Teste 2 — varredura de não-fala

Só o que foi dito entra na tela. Depois de gerar, varra o `cards.json`:

```bash
grep -oE '\([^)]*\)' PROJ/*/cards.json          # deve não retornar NADA
```

Se retornar, um evento de áudio (`(música de encerramento)`, `(risos)`, `(resmunga)`) vazou
pra legenda — corrija o filtro em `load_words()` e refaça o vídeo afetado.

## Contact sheet do lote

Para um lote, gere um frame por vídeo num momento com legenda no ar e monte a folha:

```bash
ffmpeg -y -pattern_type glob -i "qa/*.png" \
  -filter_complex "tile=5x2:margin=8:padding=8:color=white" sheet.png
```

Olhe a folha inteira. É o jeito mais barato de pegar o vídeo que saiu fora do padrão — foi
assim que o reel com o olho 45px abaixo da linha apareceu.
