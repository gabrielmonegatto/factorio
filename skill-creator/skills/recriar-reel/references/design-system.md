# Design system — template preto-roxo (validado em 2 vídeos)

Canvas 720x1280 @30fps. Tudo desenhado via Pillow em sequência PNG RGBA + 1 overlay.

## Paleta

- Fundo: gradiente vertical `#0A0512` (topo) → violeta `#542EB2` (~68%) → glow radial
  lavanda `#C9A8F8` no centro-inferior; vinheta suave nos cantos superiores;
  **grain mono ~2%** (rng normal σ2.6) para matar banding. Piso nunca 100% preto.
- Acento primário: LILÁS `(198,160,255)` — palavras de ênfase, fechamentos de lockup.
- Acento secundário: AMARELO `(240,225,74)` — 1-2 palavras pontuais no máximo.
- Pill/CTA: roxo sólido `#7C3AED`; barras escuras `(26,16,37)`; pills claras `(250,250,252)`.
- Cartelas de título: preto puro.

## Tipografia (Poppins — assets/fonts/; NUNCA Arial)

| Papel | Fonte | Tamanho | Obs |
|---|---|---|---|
| Palavra grande de lockup | Poppins BoldItalic | 86–96px | branca ou lilás |
| Título de abertura | Poppins BoldItalic | 76 / 94px | 1ª e 3ª linha |
| Linha de apoio | Poppins Regular | 46–50px | NUNCA bold, nunca <40px |
| Karaokê (1 palavra/vez) | Poppins ExtraBold | 54px | stroke escuro 3px `(34,32,40)` + sombra (0,4) |
| Pills/badges | Poppins SemiBold | 27–34px | texto escuro em pill clara |
| CTA linha 1 | Poppins SemiBold | 44px | branco em pill roxa |
| CTA linha 2 | Poppins Medium | 29px | branco em barra escura |

## Lockups (cartelas e títulos) — cascata compacta

- Ancoragem: LEFT-BASELINE (`anchor="ls"`), nunca central. Palavras de uma linha
  compartilham baseline com x acumulado por largura de prefixo (`line_positions()`
  em scripts/build_overlays.py).
- Geometria: 3 linhas em escada descendo à direita; gaps de baseline 43–67px
  (apoio ~45 abaixo da grande; fechamento ~65 abaixo do apoio). Linha 1 x≈95–115,
  apoio x≈165–225, fechamento x≈170–300.
- Padrão de cor: grande branca → apoio branco regular → fechamento GRANDE colorido
  (lilás). Ex.: "la forma / de / entregarlo", "impulsa / contenido / al azar".
- Revelação palavra a palavra no timestamp falado; a cartela persiste até o corte.

## Componentes

- **Card de vídeo**: moldura branca stroke 6px, raio 28 (16 em thumbs), corner-cover
  com o pixel do bg (paste BG.crop pela máscara inversa do rounded-rect) + drop shadow
  (blur 13, alpha 115, offset +10y). Clipes escuros dentro de card: `eq=brightness=0.06:
  contrast=1.08:saturation=1.12`.
- **Pill de views**: pill branca com ícone de olho desenhado (elipse outline + círculo)
  + "N,NM de vistas" em SemiBold escuro. Topo-esquerdo (28,150), h≈66.
- **Badges de views sob thumbnails**: mini-pill branca, olho escuro + número, h≈48,
  entrada em stagger (~0.4s entre elas).
- **Pill "Recién visto"/anotações que cobrem texto que rola**: pill roxa sólida,
  texto branco, h≈124, keyframes de y medidos frame a frame.
- **Tarja de karaokê sobre conteúdo vivo**: rounded-rect feathered (GaussianBlur 14 na
  máscara), fill `(10,8,16)` alpha 250, h≈150. NUNCA atravessar cartelas pretas
  (vira retângulo cinza visível) — dividir a janela.
- **CTA**: doc mock borrado (branco, highlights lilás, separadores) rolando para cima
  (imagem alta + crop animado) + pill roxa com a palavra-chave + barra escura com o
  benefício. Progress-bar preta opcional atrás.

## Posições de karaokê por layout

- Card grande: DENTRO do card, cy≈645–660 (com tarja).
- Card pequeno/split/therapy: ACIMA do card, cy≈210–235 (sem tarja; stroke + sombra).
- Seções gradiente sem card: cy conforme o original espelhado.
- Palavra segura até o t0 da próxima; última palavra da seção segura até o corte.
