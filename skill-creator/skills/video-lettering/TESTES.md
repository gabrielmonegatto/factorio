# Casos de teste — video-lettering

## Caso 1 — roteiro novo curto (60-90s)
Input: "cria um video lettering com esse roteiro:" + roteiro de 8-12 frases.
Esperado: beats.json coerente com a gramática (atos com acento certo, punch
words ≤3, pausas pretas), VO com timestamps, b-rolls sem texto, lettering
sincronizado à fala, mp4 em ~/Downloads, QC de brilho + frames 1fps limpo.

## Caso 2 — validação da gramática
Input: roteiro com ato de dor explícito.
Esperado: acento VERMELHO nas telas desse ato, b-rolls de angústia (não
alegres), pelo menos 1 pausa preta pós-soco.

## Caso 3 — gatilho negativo
Input: "baixei esse reels, recria em espanhol" (vídeo-modelo existe).
Esperado: NÃO dispara — recriar-reel atende.

## Status Fase 4
Pipeline inteiro validado ao vivo na produção-modelo (anúncio 275s, 82 b-rolls
Kling, 8251 frames de lettering, QC com 3 correções). Teste com roteiro NOVO
(sem modelo): PENDENTE — rodar no primeiro uso real.
