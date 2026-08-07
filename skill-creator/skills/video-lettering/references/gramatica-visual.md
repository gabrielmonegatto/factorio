# Gramática visual do video lettering — os padrões e o PORQUÊ

Destilado da engenharia reversa de um anúncio real de alta performance (275s,
82 cortes) recriado do zero em `video-use/remake3/`.

## A estrutura dramática (atos)

O roteiro típico segue: **hook → promessa → verdade dura/dor → mecanismo →
prova/história → inimigo comum → oferta → CTA**. A edição acompanha:

| Ato | Acento | Fundo dominante | Por quê |
|---|---|---|---|
| Hook/promessa | ciano | b-roll aspiracional + telas de texto | curiosidade fria, promessa "limpa" |
| Dor/verdade | vermelho | telas pretas + b-rolls de angústia | vermelho = alarme; o preto isola a frase |
| Mecanismo/prova | ciano ou vermelho | b-rolls metafóricos em sequência | mostrar, não explicar |
| Oferta | rosa/magenta | b-rolls do "palco"/produto + cards | rosa desloca do resto = novidade/desejo |
| CTA | rosa | b-roll ambiente + texto persistente + seta | repetição hipnótica do comando |

A TROCA de acento sinaliza mudança de ato sem dizer nada — é o recurso mais
barato e mais poderoso do formato.

## Quando cada tipo de tela (a decisão por beat)

- **Tela de texto (preto)**: frases de TESE — afirmações, contrastes,
  comandos ("MAS É MENTIRA", "quem entende narrativa GANHA DINHEIRO").
  O preto força atenção total na palavra. 1-3s por tela.
- **B-roll**: frases de IMAGEM — quando a narração descreve algo visualizável
  ou emocional (dinheiro, tempo, multidão, exaustão, família). O b-roll é a
  METÁFORA da frase, nunca ilustração literal boba. 2-5s.
- **Texto SOBRE b-roll**: quando a frase de tese coincide com um momento
  visual forte — texto com sombra dura por cima, sem tarja.
- **Tela preta vazia**: depois de um soco verbal, 1-4s só com áudio.
  O silêncio visual é o que faz o soco doer.
- **Punch word**: UMA palavra gigante (120-150px) colorida ocupando a tela
  ("COPIAR"). Reservar para o clímax de cada ato — mais de 3 no vídeo dilui.

## O vocabulário de b-rolls (o que "aparece no fundo" e por quê)

Metáforas recorrentes do formato, todas em estética dark/cinematográfica:
- **Dinheiro**: notas caindo em câmera lenta, mãos contando, carteira vazia
  (promessa / dor). Notas SEMPRE da moeda do público (Real p/ BR).
- **Tempo**: relógios gigantes, relógio de bolso pendurado, homem correndo.
- **Massa/manipulação**: multidões em silhueta, marionetes com fios, mão
  neon controlando a multidão, parede de TVs com olhos (vigilância/atenção).
- **Exaustão/dor**: homem no escuro iluminado pelo celular, sentado na cama,
  gritando em luz vermelha, mãos na cabeça.
- **Autoridade/mecanismo**: o personagem-símbolo trabalhando (escrevendo,
  ensinando no quadro-negro, diante do cofre), war-room com documentos.
- **Vida boa (contraste)**: família na luz dourada, casal no sofá, jantar
  farto — sempre com glow branco estourado nas bordas (sonho/idealização).
- **Referências culturais**: cena estilo "keynote 2007" (Jobs/iPhone) quando
  o roteiro cita — pastiche, não cópia (vinheta oval + letterbox + azul).
- **Oferta**: palco circular high-tech magenta com o personagem-símbolo de
  braço erguido + cards de produto verticais em fundo creme com espiral.

## Ritmo

- Corte médio a cada 2-3s (o modelo tinha 82 cortes em 275s).
- Palavra-a-palavra do lettering segue a fala EXATA (word-level da VO) —
  nunca cadência inventada.
- Movimentos de câmera nos b-rolls: slow push-in como padrão; pan lateral em
  paredes/grades; whip/motion-blur só em transições de oferta.
- Seta de scroll (duplo chevron pulsando ~1Hz) entra nos últimos 20-30s e
  fica até o fim, junto do CTA.

## Erros que quebram o formato

- Texto na tela que a voz não está dizendo naquele momento.
- B-roll claro/alegre no ato de dor (quebra a temperatura).
- Mais de uma cor de acento na mesma tela.
- B-roll com legenda/letreiro gerado dentro (proibir no prompt).
- Encher toda pausa com imagem — o formato respira em preto.
