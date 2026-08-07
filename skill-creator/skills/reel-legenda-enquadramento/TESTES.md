# TESTES — reel-legenda-enquadramento

## 1. Gatilho (10 queries, metade near-miss) — PASSOU 10/10 · 2026-07-14

Rodado em subagente, com as descriptions de 5 skills vizinhas
(`enquadramento-short`, `embedded-captions`, `video-lettering`, `legenda-rede-social`).

| # | Query | Esperado | Resultado |
|---|---|---|---|
| 1 | "põe legenda animada nesses vídeos aqui da pasta" | ESTA | ✅ |
| 2 | "reenquadra pra vertical seguindo o falante" | enquadramento-short | ✅ |
| 3 | "quero esses talking heads em 4:5 com legenda estilo reels" | ESTA | ✅ |
| 4 | "transforma esse trecho do podcast em short" | enquadramento-short | ✅ |
| 5 | "deixa o olho da pessoa no primeiro terço da tela" | ESTA | ✅ |
| 6 | "faz uma legenda que passa atrás da pessoa, tipo cinema" | embedded-captions | ✅ |
| 7 | "legenda com hyperframes nesses 9 reels" | ESTA | ✅ |
| 8 | "me gera o srt desse vídeo" | legenda-rede-social | ✅ |
| 9 | "cria um anúncio de tipografia cinética sobre pejotização" | video-lettering | ✅ |
| 10 | "corta os erros de gravação desses vídeos" | NENHUMA (etapa anterior) | ✅ |

O bloco `NÃO usar para` é o que segura 2, 4 e 6 — **não remova**. `enquadramento-short`
compartilha as palavras "reenquadra", "crop", "vertical" e brigaria pelo gatilho sem ele.

## 2. Baseline (mesma tarefa, sem a skill) — PASSA · 2026-07-14

Um subagente sem a skill produziu um plano **forte**: acertou mediana de frames, olho em
`H/3`, e até a armadilha do `transform` do GSAP. Mas embarcou três defeitos que sabemos
empiricamente que quebram:

1. `height:0` no contêiner da legenda → **camada some do render** (ele raciocinou que era
   seguro; não é — ver `exemplos.md` par 2);
2. reveal palavra-a-palavra com stagger → **descentraliza a legenda** (par 3);
3. **API do hyperframes inventada** (`--transparent`, `--width`, `window.timeline`) → ciclo
   de debug queimado (par 7).

Conclusão: a skill agrega. O baseline entrega um vídeo *quebrado* com aparência de plano
correto — que é o pior modo de falha possível. Este teste gerou o `setup.md § contrato da
composição`, que não existia antes dele.

## 3. Qualidade — PASSOU · 2026-07-14

Geometria validada em 3 aspects a partir de um mesmo source 1080×1920:

| Aspect | Alvo do olho (H/3) | Obtido | Zoom |
|---|---|---|---|
| 1:1 (1080×1080) | 360 | 360.0 | 1.0 |
| 9:16 (1080×1920) | 640 | 640.0 | 1.03 (correto: sem zoom o topo seria negativo) |
| 16:9 (1920×1080) | 360 | 360.0 | 1.0 |

Render 1:1 conferido na imagem com as linhas desenhadas: olho na vermelha, centro do bloco
de 2 linhas na ciano, fonte reescalada pra 88px. **A geometria generaliza.**

Guarda de robustez validada: transcrição de 55s contra clipe de 14s → 39 cards fora do fim
descartados com aviso, em vez de virarem lixo mudo.

## Regressões a re-rodar ao mexer nos scripts

- `captions.py` — card com evento de áudio (`grep -oE '\([^)]*\)' cards.json` deve vir vazio).
- `captions.py` — card de 2 linhas centrado na linha dos 2/3 (só aparece na imagem).
- `reframe.py` — vídeo com a pessoa filmada BAIXA no quadro (força o caminho do zoom).
