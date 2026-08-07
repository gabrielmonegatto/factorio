# Pares certo/errado — reais da produção-modelo (remake3, jul/2026)

## Erro 1: anotação de cor quebrando o parser

❌ **Errado:** dividir linhas em "/" e cortar prosa em "—" sem olhar parênteses
→ `SAIBA MAIS(rosa/magenta)` virou "SAIBA MAIS(rosa" + "magenta)" NA TELA
(14 cartelas corrompidas passaram batido até o QC de brilho).
✅ **Certo:** split de linhas e corte de prosa depth-aware de parênteses
(`split_depth0` em scripts/build_text_events.py).
**Por quê:** a anotação `(rosa/magenta)` e comentários `(azul, caps — entra
depois)` são parte da linguagem dos beats; o parser tem que engolir tudo.

## Erro 2: cartela com fundo errado

❌ **Errado:** toda tela de texto em preto — a cartela da oferta
"DOCUMENTAÇÃO FILMADA" ficou rosa-sobre-preto quando o formato pede
rosa-sobre-CREME (o ato de oferta muda o fundo).
✅ **Certo:** fundo por beat no montage (`color=0xEFE8DC` no beat da oferta).
**Por quê:** o ato da oferta inverte o esquema (claro com vinheta) de
propósito — sinaliza "agora é produto".

## Erro 3: prompt de b-roll com texto

❌ **Errado:** descrever no prompt o letreiro que aparece na cena
("card com título HARD ADS em vermelho") → o gerador escreve texto torto.
✅ **Certo:** prompt SÓ do fundo visual + "No text, no captions, no
watermarks"; todo texto entra pela camada de lettering.
**Por quê:** texto gerado por IA de vídeo é ilegível/mutante; o lettering
nosso é vetorial, sincronizado e editável.

## Erro 4: QC de "buraco" corrigindo cena legítima

❌ **Errado:** brilho <8 num beat de b-roll → sair regenerando o clipe.
✅ **Certo:** conferir o frame primeiro: o corredor de dados monocromático e
o macro dos óculos ERAM escuros por design; só a cartela 226 era buraco real.
**Por quê:** o formato é dark — luminância baixa é a regra, não a exceção.
A régua é "original/intenção clara vs preto ABSOLUTO".

## Erro 5: infraestrutura frágil em produção longa

❌ **Errado:** produzir horas de assets no scratchpad de /tmp → a sessão caiu
e apagou TUDO (8k frames de type, storyboard, prompts, fila).
✅ **Certo:** produção longa mora no repo (`video-use/<projeto>/`); o que se
perder recupera dos journals de workflow e transcripts de agente em ~/.claude.
**Por quê:** scratchpad é por-sessão e volátil; render de 275s não é.

## Erro 6: pollar geração job a job

❌ **Errado:** 73 chamadas de job_status para pegar 73 URLs.
✅ **Certo:** `show_generations(size:100)` → todas as URLs num arquivo →
extrair com python → curl em lotes de 8.
**Por quê:** cada roundtrip de MCP custa tempo e contexto; a listagem é 1 chamada.

## Shot-list de referência (frase → metáfora → prompt)

- "é o tempo que eu preciso pra te mostrar" → homem correndo diante de
  relógio gigante, P&B vintage 1950s, grão pesado, câmera travada.
- "5 mil reais por mês na internet" → homem sorrindo de olhos fechados com
  notas de Real caindo em câmera lenta, facho duro de cima, fundo preto.
- "todo mundo te ensinou que copiar é o caminho" → multidão em silhueta
  hipnotizada diante de um homem elevado num feixe de luz, halftone P&B.
- "o algoritmo não empurra conteúdo à toa" → marionetes penduradas em fios
  sob uma mão gigante, névoa teal, palco de pedra.
