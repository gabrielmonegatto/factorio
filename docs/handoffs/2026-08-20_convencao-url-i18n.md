# Handoff — convenção de URL (i18n) no mananciall-site — 20/08/2026

> **Para a outra sessão que está mexendo na loja.** Regra nova no repo, decidida
> hoje porque duas sessões editando sem convenção escrita vira divergência.

## A regra

**O caminho da URL segue o idioma DA PÁGINA.**

| Idioma | Onde mora | Caminho |
|---|---|---|
| EN (padrão) | raiz | em inglês: `/books`, `/collections`, `/library`, `/preacher/spurgeon` |
| PT | sob `/pt/` | em português: `/pt/livros`, `/pt/colecoes`, `/pt/biblioteca` |

Neutros (não traduzem): `/go/*`, `/api/*`, `/read/*`.

Identificador dentro do código continua em português (`canal`, `oferta`, `preco`).
URL é interface pro usuário e pro buscador; nome de variável não é.

Escrita no `CLAUDE.md` do próprio repo do site (seção "Convenção de URL"),
que é o que a sessão de lá lê ao abrir.

## O que mudou hoje neste repo

- Nasceu `/pregador/spurgeon` servindo página em inglês. **Renomeado pra
  `/preacher/[canal]`** no mesmo dia, antes de indexar.
- Rotas novas: `/go/<canal>` (redirect + log em `go_scans`) e
  `/preacher/<canal>` (biolink com máx. 3 ofertas).
- Commits: `7a155f2` (funil /go), `7da411a` (biolink), `d8e8229` (convenção).

## 🧨 GOTCHA que custou um deploy errado

**Build incremental do Astro mantém rota deletada no `dist/` e ela vai pro deploy.**
Depois de `git mv` da rota, `/pregador/spurgeon` continuou respondendo **200** em
produção. E, no mesmo build sujo, a rota nova `/preacher/moody` dava 404.

Antes de qualquer deploy que **renomeia ou remove rota**:

```bash
rm -rf dist .astro && pnpm run build
```

## Se precisar mexer no funil

- Destino por canal: mapa `DESTINO` em `src/pages/go/[...canal].ts`
- Ofertas por canal: mapa `CANAIS` em `src/pages/preacher/[canal].astro`
- Os dois moram junto do código de propósito: trocar é deploy de 1 linha e o
  QR impresso nos vídeos nunca muda.
- `/go` sem canal É `spurgeon` pra sempre (QRs já publicados). Não "consertar".

## Pendências que ficam pra loja

- [ ] Produto de **combo/bundle** do Spurgeon não existe (coleção no D1 não tem
      preço). Hoje a 3ª oferta do biolink é "ver a biblioteca". Bundle de verdade
      precisa de produto no Paddle → gate do Gabriel.
- [ ] Nenhum título do **Moody** na livraria: `/preacher/moody` cai na biblioteca
      geral. Criar antes do canal do Moody lançar.
- [ ] Descrição da coleção `spurgeon-library` diz "Twelve complete volumes" e
      vai ficar desatualizada: a mineração está trazendo os 63 volumes.
