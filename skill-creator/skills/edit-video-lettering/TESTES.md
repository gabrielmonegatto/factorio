# Casos de teste — edit-video-lettering

## Caso 1 — montagem completa
Input: "monta esse video lettering no palmier" + pasta com gen/, áudio, storyboard.
Esperado: projeto 9:16 criado, clipes nos beats exatos, lettering no topo,
b-rolls mutados, export estabilizado em ~/Downloads, timeline editável no app.
Validado ao vivo: projeto "Anuncio Narrativa ES" (10-11/07/2026, 4 exports).

## Caso 2 — captions nativas modeladas
Input: "coloca como captions no palmier, mas só onde o original tem legenda".
Esperado: add_captions + filtro por janelas (loop janelado até limpo),
estilo karaokê (wordReveal + highlight), track ProRes oculta de reserva.
Validado ao vivo: 309→133 clips, 3 rounds.

## Caso 3 — gatilho negativo
Input: "cria um video lettering com esse roteiro" (gerar assets).
Esperado: NÃO dispara — video-lettering atende; esta skill entra depois,
se o usuário pedir a montagem no Palmier.
