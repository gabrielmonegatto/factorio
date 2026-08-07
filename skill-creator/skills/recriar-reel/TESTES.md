# Casos de teste — recriar-reel

## Caso 1 — Modo A (tradução por cima)
Input: "baixei um reels em inglês, quero ele em espanhol" + mp4 de análise-de-viral.
Esperado: mp4 em ~/Downloads; zero texto EN do editor visível (QC 1fps); legendas saem
nos cortes; música original nas janelas limpas + bed tratado sob a VO; voz Alejandro.
Validado ao vivo: reel_patron_viral_ES_v2.mp4 (10/07/2026).

## Caso 2 — Modo B (recriação do zero)
Input: "recria esse vídeo do zero com nossa paleta" + mp4.
Esperado: nenhum frame do design original; clipes extraídos limpos; template preto-roxo;
tipografia Poppins nas medidas; lockups em cascata; CTA com pill roxa; 1239/1291 frames
exatos no ffprobe. Validado ao vivo: reel_patron_viral_ES_v4.mp4 e reel_formatos_ES_roxo.mp4.

## Caso 3 — Gatilho negativo
Input: "corta os erros dessa minha gravação de talking head".
Esperado: recriar-reel NÃO dispara (talking-head-recut/video-use atendem).

## Status Fase 4
Pipeline validado ao vivo em 2 vídeos completos (4 iterações + 2 rodadas de correção
de tipografia). Testes de gatilho em sessão nova: PENDENTES.
