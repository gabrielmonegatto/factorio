# 🖼️ GERAÇÃO DE IMAGEM — o que funciona e o que não funciona

> Investigado em 20/08/2026, testando de verdade contra a nossa conta.
> Nasceu do problema real: os bustos do Moody saíram como um senhor vitoriano
> genérico, praticamente idêntico ao busto do Spurgeon.

---

## 1. O problema: texto não sabe a cara de ninguém

Modelo text-to-image não conhece a fisionomia de personagem histórico. Pedir
"retrato de D.L. Moody" devolve **um homem vitoriano de barba qualquer**. Com
10 canais de pregadores diferentes, todos ficam com a mesma cara — o que quebra
a regra de identidade por canal (doc 19).

A solução da categoria é **image-to-image**: partir de uma foto real (ou de um
retrato aprovado) em vez de inventar do zero.

---

## 2. Infra que já existe e FUNCIONA

**Worker `factorio-imagens`** (`tools/imagens/`), no ar.

- Gera via binding `env.AI.run` e grava direto no R2
- **Por que um Worker e não a API REST:** o `CLOUDFLARE_API_TOKEN` do `.env`
  tem D1 e Workers mas **NÃO tem Workers AI** (a REST responde 401). O binding
  não usa token de API.
- Protegido por `FACTORIO_IMAGENS_SEGREDO` (no `.env`)
- `POST /gerar {chave, prompt, modelo?, imagem_b64?, forca?}`

✅ **Text-to-image validado:** 27 assets do Moody gerados com
`@cf/black-forest-labs/flux-1-schnell`, 0 falhas.

### 🧨 Minas descobertas

| Mina | Sintoma | Conserto |
|---|---|---|
| Token sem Workers AI | REST devolve 401 | usar Worker com binding |
| `workers.dev` bloqueia bot | **403** com urllib | mandar `User-Agent` próprio |
| `sd-1.5-img2img` recusa imagem grande | `3040: Unknown error` com 1024px | **redimensionar pra 512px** |
| `flux-2-klein` não aceita JSON | `required properties at '/' are 'multipart'` | schema multipart não documentado; FormData no binding NÃO resolveu |

---

## 3. Image-to-image na Cloudflare: BLOQUEADO hoje

| Modelo | Estado |
|---|---|
| `@cf/runwayml/stable-diffusion-v1-5-img2img` | schema OK a 512px, mas **"Capacity temporarily exceeded"** em 5 tentativas seguidas |
| `@cf/black-forest-labs/flux-2-klein-4b` / `-9b` | exige `multipart`, formato não documentado; FormData via binding rejeitado |

**Diagnóstico honesto:** o img2img da Cloudflare ou está sem capacidade, ou tem
schema que a doc pública não expõe. Não dá pra depender dele hoje.

---

## 4. Alternativas (fora da Cloudflare)

| Caminho | Custo | Preserva semelhança | Nota |
|---|---|---|---|
| **Gemini (imagem)** | pago por imagem | ⭐ excelente em edição com referência | Gabriel **já usa manualmente** pra thumb; tem API |
| **Replicate** (`flux-kontext-pro`, `instant-id`) | ~centavos/imagem | ⭐ feito pra identidade | API simples, paga por uso |
| **Foto histórica direto** | grátis | 100% (é a pessoa) | Moody morreu em 1899: fotos em DP. Restaurar/tratar em vez de gerar |

**Recomendação: foto histórica + tratamento.** Pregador de canal Treasures morreu
antes de 1930 por definição (é o critério de licença do doc 18), então SEMPRE
existe foto em domínio público. Usar a foto real resolve semelhança, licença e
diferenciação de uma vez — e não depende de modelo nenhum.

O gerador entra só pra padronizar (fundo preto, luz quente), e aí um img2img
leve basta. Se a Cloudflare destravar, ótimo; senão, Gemini ou Replicate por
uns centavos, uma vez por canal (5 bustos).

---

## 5. Assets compartilhados entre canais (decisão pendente)

Pergunta do Gabriel: fundos e trilha não poderiam ser um pool grande servindo
todos os canais?

**Trilha: já é compartilhada** (`_globalassets/worship/`, 4 faixas). Funciona.

**Fundo: dá, mas com um porém.** Um pool de centenas de fundos genéricos de
igreja de época serve tecnicamente qualquer canal. Só que a diferenciação
visual entre canais hoje vem **justamente do fundo** (catedral gótica fria no
Spurgeon vs salão âmbar no Moody) — porque o busto saiu igual nos dois.

Meio-termo que resolve os dois lados:

- **Pool global grande** (centenas), com **subconjunto por canal** filtrado por
  ambiente/paleta. Cada canal puxa só da sua fatia.
- Gera-se muito de uma vez (é barato e paralelo), e canal novo só escolhe a fatia.
- ⚠️ Se todos os canais usarem o mesmo pool inteiro, eles ficam visualmente
  intercambiáveis, e aí "10 canais" vira "1 canal em 10 endereços".
