---
name: video-lettering
description: >
  Cria do zero um vídeo de tipografia cinética estilo "anúncio dark" (video
  lettering) a partir de um ROTEIRO: gera a locução (ElevenLabs), a trilha,
  os b-rolls cinematográficos por IA (Higgsfield/Kling) e o lettering
  palavra-a-palavra sincronizado à voz, com direção de arte por atos
  (ciano→vermelho→rosa). Entrega mp4 720x1280@30 em ~/Downloads.
  TRIGGER quando o usuário disser "cria um video lettering", "vídeo lettering
  com esse roteiro", "faz um vídeo desse tipo com esse roteiro", "vídeo de
  tipografia estilo anúncio dark", ou entregar um roteiro pedindo esse formato.
  NÃO usar quando existe um vídeo-modelo para recriar/traduzir — para isso
  use recriar-reel.
---

# video-lettering

Recebe um roteiro (PT-BR por padrão) e produz um anúncio dark de tipografia
cinética: voz narrada gerada, música tensa de fundo, telas de texto em preto
alternando com b-rolls cinematográficos gerados por IA, tudo cortado no ritmo
da fala. Formato validado na recriação de um anúncio real de 275s (remake3).

## Regras duras

1. **Uma ideia por tela.** Cada tela de texto carrega UMA frase/fragmento;
   palavras entram NO timestamp falado com ramp de luminância de 180ms
   (cinza 30% → cor). Texto que atravessa o corte da cena reprova.
2. **Cor é dramaturgia**: branco = base; UMA cor de acento por ato —
   ciano `(20,190,240)` no ato de promessa/curiosidade, vermelho `(240,18,16)`
   na dor/verdade dura, rosa `(243,23,161)` na oferta/CTA. Acento só em
   palavras-chave (1-3 por tela), com glow. Nunca misturar acentos numa tela.
3. **B-roll é metáfora, não decoração.** Cada b-roll traduz visualmente a
   frase narrada naquele momento (dinheiro caindo = promessa; multidão = massa;
   relógio = tempo). Prompt de geração NUNCA contém texto/letreiro
   ("no text, no captions, no watermarks" sempre).
4. **Personagem-símbolo recorrente**: eleja 1 figura conceitual (ex.: homem de
   terno com cabeça de câmera de vigilância) e descreva-a SEMPRE com a mesma
   frase no prompt — é o fio visual da marca no vídeo.
5. **Pausa preta é ferramenta**: 1-4s de tela preta após frases de impacto.
   Não preencher tudo.
6. **Coesão de textura**: todo prompt de b-roll termina com o style tail padrão
   (9:16, dark ad, film grain, deep shadows); vinheta global no render final.
7. **ffmpeg**: um `-i` por uso, segmentos com `trim=end_frame=K` somando o
   total exato, texto via PNG Pillow (sem drawtext). QC SEMPRE na timeline
   inteira + checagem de brilho por segundo vs esperado.

## Workflow

1. **Direção** — leia `references/gramatica-visual.md`. Divida o roteiro em
   atos e beats (2-4s cada): para cada beat decida `texto` / `broll` /
   `preto`, escreva as telas de texto com anotação de cor
   (`PALAVRA(branco) / CHAVE(ciano)`) e a descrição visual dos b-rolls.
   Output: `beats.json` (mesmo schema do storyboard: start_s/end_s/kind/
   texto_linhas/broll_descricao/movimento/extras).
2. **Locução** — gere a VO por frase com ElevenLabs `/with-timestamps`
   (voz grave de autoridade; PT: buscar shared-voices `language=pt` mais usada,
   validar com o Pedro na 1ª execução). Monte a timeline de áudio e TRAVE os
   tempos dos beats nos tempos reais da fala. Script-modelo: `scripts/gen_tts.py`.
3. **Trilha** — dark phonk/tensão via ElevenLabs Music, nivelada sob a VO
   (rms alvo ~0.07, piso 0.065), fade-out no fim.
4. **Shot list** — converta cada broll_descricao em prompt EN de 60-110
   palavras (sujeito, enquadramento, luz, paleta, movimento) + style tail.
5. **Gerar b-rolls** — Higgsfield `kling3_0_turbo`, 9:16, 5s (10s p/ cenas
   longas), ondas de ~8 com `declined_preset_id` fixo; ao final, pegue TODAS
   as URLs com `show_generations size=100` (nunca pollar job a job); baixe
   como `gen/b{idx:03d}.mp4`. Cena de motion-graphics simples (ícones) =
   renderizar local com Pillow, não gerar.
6. **Lettering** — `scripts/build_text_events.py` (casa palavras com o
   word-level da VO; parser de anotações é depth-aware de parênteses) +
   `scripts/render_type.py` (Anton, specs em `references/specs-tecnicas.md`).
7. **Montagem** — `scripts/montage.py`: segmento por beat com frame cap exato,
   ping-pong loop em clipes curtos, fundo especial por beat quando não-preto,
   concat → overlay do type → vinheta → mux da VO+trilha.
8. **QC** — `nb_read_frames` exato; frames 1fps da timeline INTEIRA;
   brilho/segundo vs esperado (preto onde devia ter b-roll = buraco);
   transcrever o output e conferir cada frase na sua janela; boundaries a 100ms.
9. **Entrega** — `~/Downloads/<nome>.mp4` + relatório com atos e timestamps.

## Graus de liberdade

- **Fixo**: pipeline e QC acima, specs de tipografia, style tail, guardrails
  de ffmpeg, "prompt sem texto", trabalho em DISCO PERSISTENTE (nunca /tmp —
  sessão que cai apaga o scratchpad).
- **Livre**: divisão em atos e ritmo dos beats, escolha das metáforas visuais,
  personagem-símbolo, paleta alternativa se o Pedro pedir, voz, duração.

## Ponteiros

- `references/gramatica-visual.md` — ANTES do passo 1: os padrões do formato
  e o porquê de cada um.
- `references/specs-tecnicas.md` — ANTES dos passos 5-7: tipografia, prompts,
  música, ffmpeg.
- `references/exemplos.md` — pares certo/errado reais da produção-modelo.
- `scripts/` — pipeline funcional completo (adaptar paths, não reescrever).
- `assets/fonts/` — Anton (lettering) embarcada.
