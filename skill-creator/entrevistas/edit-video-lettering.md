# Entrevista — edit-video-lettering (extraída da montagem ES no Palmier, 10-11/07/2026)

1. **Job**: assets de video lettering → projeto montado e exportado no Palmier
   Pro (timeline editável). Pronto = mp4 exportado + projeto aberto no app.
2. **Gatilhos**: "quero recriar ele pelo palmier-pro", "consegue botar como
   captions?", "atualizou no palmier?", "monta/edita no palmier".
3. **Barra**: legenda SÓ onde o vídeo-modelo tem legenda; b-rolls sem áudio
   fantasma; export = o que está na timeline; nada duplicado após drops.
4. **Modos de falha reais**: transport drop tratado como falha (duplicaria
   imports); esperar servidor mudo sem probe; "clips"/"track" em vez de
   entries/trackIndex; captionDetail lido uma vez só (sobram captions fora
   das janelas); fonte não instalada.
5. **Expertise**: playbook da API vivida (references/palmier-playbook.md) +
   client HTTP próprio (scripts/palmier.py).
6. **Liberdade**: captions nativas vs ProRes vs híbrido; estilo; destino.
7. **Contexto**: Palmier Pro local (MCP http 127.0.0.1:19789), ffmpeg p/
   ProRes 4444, fontes em ~/Library/Fonts.
8. **Output**: mp4 + projeto .palmier + relatório de tracks.
