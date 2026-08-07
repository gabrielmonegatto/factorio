# funnel-matrix: o registry shadcn da Br4nds

A fábrica de páginas da linha de montagem (Área 2 do `LINHA_DE_MONTAGEM_CRO.md`).
Decisão de 07/08/2026: em vez de "pasta pra copiar", os componentes de funil
viram um **registry shadcn**: qualquer projeto instala com
`npx shadcn add @br4nds/<componente>`, e o CLI traz as dependências junto.

Status: 🟡 esqueleto. O `registry.json` está vazio até a extração da Bluue
(plano em `EXTRACAO.md`). Não anunciar como pronto.

## Arquitetura de 3 camadas (quem fornece o quê)

| Camada | Fonte | Por projeto |
|---|---|---|
| Componentes de funil | ESTE registry | nunca muda (é a matriz) |
| Blocos genéricos (hero, FAQ, pricing) | Tailark (grátis) · Shadcnblocks (pago) · Magic UI | escolhe por página |
| Tema + copy + imagens | tweakcn.com (tokens) · content files | sempre muda |

Regras que fazem a matriz funcionar:
1. **Copy NUNCA dentro de componente.** Todo texto entra por props/content file
   (`content.base.mjs`): é o que torna a página testável por A/B de graça.
2. **Cor NUNCA chumbada.** Só tokens do tema (`--primary` etc.). Componente com
   hex hardcoded não entra no registry.
3. **Tracking embutido**: componente de funil que gera evento (CTA, resposta de
   quiz) já chama `window.croTrack()` do cro-stack. Matriz e motor andam juntos.

## Como servir o registry

Repositório GitHub público com `registry.json` na raiz já funciona no CLI do
shadcn (GitHub registries). Evolução: namespace `@br4nds` com auth por header
(shadcn 3.0) quando houver componente que não pode ser público.

## Como consumir num projeto novo

```bash
npx shadcn init            # se o projeto ainda não tem components.json
npx shadcn add @br4nds/quiz-engine
```

(Enquanto o namespace não está publicado, aponta-se a URL do registry direto no
`components.json` → `registries`.)
