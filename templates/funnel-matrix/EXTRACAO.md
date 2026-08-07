# Plano de extração: Bluue → funnel-matrix

A Bluue é o laboratório mais maduro; estes componentes provaram valor em
produção com tráfego pago e são candidatos ao registry, NESTA ordem (do mais
reaproveitável pro mais acoplado):

| Ordem | Item do registry | Fonte na Bluue (`apps/br4nds/bluue/src/`) | Trabalho de limpeza |
|---|---|---|---|
| 1 | `trust-carousel` | `components/` (carrossel de influenciadores da /pastilha e /ps) | trocar imagens por props; remover azul #00B4E5 |
| 2 | `consent-popup` | popup de termos usado na tela 4 do quiz e na `ps-lp/PsLanding.tsx` | texto por props; iframe de termos por prop |
| 3 | `lp-squeeze` | `components/ps-lp/PsLanding.tsx` + `copy.ts` | já nasceu com copy externa (modelo a seguir); generalizar destino do CTA |
| 4 | `pre-checkout` | `components/quiz/QuizPreCheckout.tsx` | separar embed vs redirect por config (`checkout_embed`); remover oferta hardcoded |
| 5 | `quiz-engine` | `components/QuizEngine.tsx` + `components/quiz/*` + `content/quiz.base.mjs` | o maior: separar motor (navegação, `?p=`, dataLayer) das telas da Bluue |
| 6 | `advertorial` | `lp-motivos/PaginaMotivos.tsx`, `lp-cinco/PaginaCinco.tsx` | estrutura vira template; copy/imagens 100% por props |

Regras de limpeza (bloqueantes pra entrar no registry):
- Zero hex de cor: tudo via token (`--primary`, `--secondary`...). A Bluue tem
  #00B4E5 chumbado em vários pontos: limpar na extração, 1×.
- Zero texto de marca: copy por props ou content file.
- Zero import de asset de marca: imagem entra por prop (lembrar do gotcha Astro:
  import de imagem retorna ImageMetadata; pra string usar `?url`).
- Nome de arquivo/chunk sem "adv" (adblock bloqueia por nome).
- Evento de interação já chama `window.croTrack()` (contrato do cro-stack).

Cada item extraído entra no `registry.json` com `type: "registry:component"` (ou
`registry:block` pros compostos) e é testado com `npx shadcn add` num projeto
limpo ANTES de ser anunciado.
