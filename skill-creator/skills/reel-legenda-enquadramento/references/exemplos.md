# Pares certo/errado

Todos são erros que ACONTECERAM de verdade na produção dos reels da Juliana Guerra
(2026-07). Cada par ensina um modo de falha diferente.

---

## 1. Centralização vertical: quem posiciona não pode ser quem anima

**ERRADO** — o GSAP anima `transform` e apaga o `translateY(-50%)` que centralizava:

```css
.cap{ position:absolute; top:960px; transform:translateY(-50%); }
```
```js
tl.fromTo("#g0", {y:14, scale:.94}, {y:0, scale:1});   /* transform sobrescrito */
```
Resultado: o **topo** do bloco cai na linha dos 2/3, não o centro. A legenda desce
~40px e ninguém percebe no código — só na imagem.

**CERTO** — o clipe posiciona (e ocupa o frame inteiro); o filho anima:

```css
.cap{ position:absolute; left:0; top:0; width:1080px; height:1440px;
      padding-top:480px;                    /* caixa de conteúdo = 960..1440 */
      display:flex; align-items:center; }   /* centro do card = 960 = 2H/3 */
.txt{ width:100%; text-align:center; }
```
```js
tl.set("#c0",{autoAlpha:1});                /* .cap: só alpha */
tl.fromTo("#g0",{opacity:0,y:14},{opacity:1,y:0});   /* .txt: transform */
```
`padding-top = 2·(2H/3) − H` faz o `align-items:center` cravar o centro do card em `2H/3`,
com 1 ou 2 linhas, em qualquer aspect.

---

## 2. Clipe de altura zero some do render

**ERRADO** — parece elegante (uma "linha" de altura zero pra centrar em cima dela):

```css
.wrap{ position:absolute; top:960px; height:0; display:flex; align-items:center; }
```
O engine recorta o clipe à sua caixa → altura 0 → **camada inteira em branco**. O render
"funciona", não dá erro, e entrega vídeo sem legenda nenhuma.

**CERTO** — clipe do tamanho do frame, deslocamento por `padding-top` (ver par 1).

---

## 3. Palavra a palavra descentraliza a legenda

**ERRADO** — cada palavra aparece só quando é falada:

```js
tl.fromTo("#g0w2",{opacity:0},{opacity:1}, 17.5);   // palavra 3 de 4
```
As palavras ainda invisíveis (`opacity:0`) **continuam ocupando espaço**. O texto visível
encosta à esquerda e a legenda parece desalinhada, card após card.

**CERTO** — karaokê: o card entra inteiro (centrado e estável) e cada palavra dá um pop no
instante em que é dita. A ênfase bate mais forte (1,14× contra 1,08×).

```js
tl.set("#c0",{autoAlpha:1}, gin);                                  // card inteiro
tl.to("#g0w2",{scale:1.08,duration:.09}, w.start);                 // pop na fala
tl.to("#g0w2",{scale:1,duration:.14}, w.start+.09);
```

---

## 4. Evento de áudio virando legenda

**ERRADO** — filtrar só o espaçamento:

```python
ws = [w for w in t["words"] if w.get("type") != "spacing"]
```
O Scribe emite eventos de áudio como tokens próprios. Foi ao ar um card escrito
**`(MÚSICA DE ENCERRAMENTO)`** no fim de um reel. Também aparece `(resmunga)`, `(risos)`.

**CERTO** — lista de permissão, não lista de bloqueio, mais uma segunda barreira:

```python
ws = [w for w in t["words"]
      if w.get("type") == "word" and "(" not in w["text"]]
```

---

## 5. O olho não chega no primeiro terço só recortando

**ERRADO** — assumir que todo vídeo alcança o alvo cortando, e aceitar o "quase":

```python
top = min(480, eye - 480)      # satura em 480 e entrega o olho em y=525
```
Num reel a pessoa foi filmada baixa no quadro (olho em y=1005 de 1920). O corte satura e o
olho para 45px abaixo da linha — erro silencioso, só um dos 9 vídeos sai fora do padrão.

**CERTO** — calcule o menor zoom que torna o alvo alcançável e aplique (`plan()` em
`reframe.py`). No caso real, zoom 1,06× cravou o alvo. Um vídeo com zoom mínimo é melhor
que nove no padrão e um fora.

---

## 6. Constante cravada em vez de fórmula

**ERRADO** — a skill nasceu no 3:4 e ficou com os números do 3:4:

```python
EYE_Y, CAPTION_Y, FONT = 480, 960, 88
```
No 9:16 o olho vai pro lugar errado (deveria ser 640) e a legenda também (1280). Quebra em
silêncio: o vídeo sai, só está mal enquadrado.

**CERTO**:

```python
eye_y     = h / 3
caption_y = 2 * h / 3
font      = 0.0815 * min(w, h)   # relativo ao MENOR lado: mesma presença em qualquer aspect
```

---

## 7. Inventar a API do hyperframes

**ERRADO** — flags plausíveis, que não existem (isto saiu de um teste de baseline real):

```bash
hyperframes render comp.html --width 1080 --height 1350 --duration 43 --transparent -o x.webm
```
```js
window.timeline = tl;          // a chave certa é window.__timelines["<composition-id>"]
```

**CERTO** — dimensão, duração e transparência vivem no HTML, não na linha de comando:

```bash
npx hyperframes render . --format webm -f 24 -o cap.webm
```
Contrato completo em `setup.md`. Escrito de memória, o modelo alucina essas flags — leia o
contrato antes de mexer no gerador de composição.

---

## 8. Palavra funcional pendurada no fim do card

**ERRADO** — cortar a cada N palavras:

```
É TUDO ISSO QUE        MULTA DE QUARENTA POR
VOCÊ PAGA QUANDO O     CENTO
```

**CERTO** — quebrar preferindo a vírgula do transcript, e nunca fechar em palavra funcional:

```
É TUDO ISSO            INSS PATRONAL
QUE VOCÊ PAGA          MULTA DE QUARENTA POR CENTO
```
