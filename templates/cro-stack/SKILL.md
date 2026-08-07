---
name: stack-conversao
description: Instala a estrutura de conversão completa (sessão first-party, eventos server-side, casamento de venda, teste A/B, backup, QA e virada de domínio) em qualquer projeto novo, dentro ou fora da Br4nds. Use quando pedirem pra montar tracking ou atribuição pra marca nova, replicar a estrutura da Bluue, plugar domínio novo, ou preparar e executar virada de domínio com anúncio ativo.
---

# Stack de conversão — instalação completa

Extraída da operação real da Bluue (R$40k+/semana em tráfego). Cada regra aqui
custou dinheiro ou quase custou. O kit de arquivos vive em
`_factorio/templates/cro-stack/`; a implementação-modelo, sempre mais viva que o
kit, é `apps/br4nds/bluue`.

## O ciclo que ela fecha

```
anúncio ─→ clique (fbclid) ─→ PORTEIRO cria sessão + crachá (_fbp/_fbc)
                                   │
                              páginas do funil ─→ eventos internos (etapas)
                                   │                e canônicos (Lead, IC) → CAPI
                              checkout leva sck = id da sessão
                                   │
                       venda PAGA volta do caixa (webhook/API)
                                   │
                       WORKER casa venda ↔ sessão pelo sck
                                   │
              Purchase no pixel certo, com o NOME certo e 14 parâmetros
```

O que faz esta stack valer mais que um pixel no navegador: **a venda sobe do
caixa, não da tela de obrigado** (metade das vendas é pix pago com a aba
fechada), e **cada venda casa deterministicamente com a sessão que a gerou**
(pelo `sck`, não por email, que falha quando a pessoa compra com outro email).

## Os 7 princípios (o porquê antes do como)

1. **Sessão nasce no servidor.** O porteiro (middleware) cria `_bnd_sid`,
   `_fbp` e `_fbc` antes de qualquer JS rodar. Bloqueador não alcança, e 100%
   das visitas têm identidade.
2. **Config declara FATO, não categoria.** "A raiz deste domínio serve
   /quiz/v1/", nunca "este domínio é do tipo funil". Categoria envelhece e o
   código deduz errado.
3. **1 venda = 1 evento.** `event_id = sale_id`, com livro-caixa
   (`purchases_sent`) que registra cada envio e recusa duplicata.
4. **Falha abre.** Motor de A/B, scripts de terceiro, config: qualquer erro
   devolve a página normal. Quem paga a página quebrada é o anúncio.
5. **O pixel recebe hoje o que recebia ontem.** Nome de evento E parâmetros.
   Conjunto ativo otimiza num evento custom com nome herdado (ex.: `p`); EMQ
   alto vem de mandar TODOS os parâmetros. Qualquer regressão nisso derruba
   campanha sem ninguém ter tocado em campanha.
6. **Compare conteúdo RENDERIZADO, nunca título ou nome de arquivo.** Páginas
   do mesmo site herdam o `<title>` do layout; SPA serve casca vazia. As duas
   comparações por rótulo feitas na migração da Bluue estavam erradas e uma
   iria mandar 16 anúncios pra página errada.
7. **Anúncio ativo é intocável.** URL de anúncio não se edita (volta pra
   revisão e zera aprendizado). A estrutura muda POR BAIXO do anúncio: DNS,
   rotas, config.

---

## Nível de instalação

| Cenário | O que fazer | Custo |
|---|---|---|
| Marca nova na MESMA conta Cloudflare | 1 INSERT em `domain_config` + secret `META_TOKEN_<MARCA>` + domínio no projeto Pages | minutos |
| Projeto novo (outra conta, cliente, parceiro) | Fases 0 a 8 abaixo | 1 a 2 dias de encanamento |

---

## FASE 0 · Coleta (antes de tocar em qualquer código)

Respostas erradas aqui viram erro silencioso depois. Colete por API e por
RENDERIZAÇÃO, nunca por suposição:

1. **Domínios e papéis.** Pra cada domínio: o que a RAIZ serve? Abra no
   navegador e leia o conteúdo. Na Bluue, `bluue.io/` tinha título de home e
   servia o quiz.
2. **Anúncios ativos.** Liste destinos exatos via API da Meta **com paginação**
   (`paging.next`: a API devolve poucos por página sem avisar que há mais, e
   também aplica mal filtros de status: confira `effective_status` linha a
   linha). Anote: caminhos, contagem por caminho.
3. **Pixel e evento de otimização.** Por conjunto ativo:
   `promoted_object.pixel_id` + `custom_event_str`. É comum otimizarem num
   evento custom de nome curto herdado de ferramenta antiga (`p`, `a_t_c`).
   Esse nome é sagrado.
4. **EMQ atual.** Print do painel do pixel: quais parâmetros chegam e em que
   percentual. É a linha de base que a Fase 3 tem que igualar.
5. **Checkout.** Plataforma, campo de repasse que volta na venda (`sck`,
   `src`, `custom_id`), como a venda paga volta (webhook? API de consulta?), e
   **o fuso do banco deles** (a B4You grava hora local SEM fuso; comparar com
   `NOW()` UTC encolhe janelas em 3h).
6. **Rastreio atual.** Stape/GTM/pixel no navegador? Quem alimenta o pixel
   hoje? Ele só morre DEPOIS da paridade provada (Fase 8).

## FASE 1 · Banco (D1)

Aplicar `d1/*.sql` na ordem. O que cada tabela é:

| Tabela | Papel |
|---|---|
| `domain_config` | 1 linha por domínio: pixel, `event_map`, `root_route`, `scripts`, checkout embutido, Clarity. É o que torna domínio descartável: trocar domínio = 1 INSERT |
| `data_tracker` | todo evento: PageView, etapas do funil, canônicos. Com sessão, crachás e variante de A/B |
| `quizzes`/leads | respostas capturadas, COM `session_id` (sem ele a venda não chega nas respostas) |
| `purchases_sent` | livro-caixa de vendas: casamento, envio, resposta da Meta. Dedup e auditoria |
| `experiments` | testes A/B. O banco RECUSA teste sem hipótese e encerramento sem decisão (CHECKs) |

## FASE 2 · Porteiro (`functions/_middleware.js`)

O coração. Em cada requisição de página: cria/renova sessão e crachás, resolve
a rota da raiz (`root_route`), sorteia variante de A/B, injeta conteúdo de
variante e scripts de terceiro no HTML, grava o PageView.

Regras que não são opcionais:

- **404 real obrigatório** (`src/pages/404.astro`). Sem ele, caminho
  desconhecido responde 200 com HTML de outra página. Combinado com
  `/_astro/* immutable`, um chunk pedido durante janela de deploy recebe HTML
  200 e o navegador **grava o HTML como se fosse o módulo por 1 ano**. Tela
  branca permanente pra quem visitou na hora errada, invisível em curl. Foi o
  pior bug da Bluue.
- **Só grava pageview de resposta < 400** (robô varrendo `/.env` não vira
  funil).
- **`scripts` é agnóstica** (JSON `[{"src":...}]` por domínio). Tag de
  terceiro (Popsixle, GTM) entra por config, injetada no `<head>` pelo
  servidor. Sem coluna com nome de fornecedor, sem `if` no código.
- **Cache de config de 60s no isolado**, e falha de leitura NÃO entra no cache
  (um soluço de 1s no banco não pode apagar a config por 60s).
- **Sem adapter Cloudflare no Astro** (`output: 'static'`). O adapter gera
  `dist/_worker.js` e o Pages ignora `functions/` inteiro em silêncio.
- **Nome de chunk sem "adv"**: bloqueador de anúncio derruba script cujo nome
  casa com `adv`/`advert`. Página `/adv-one` pode existir; arquivo
  `AdvOnePage.js` não.
- **BUILD_TAG**: constante usada no DOM de componentes críticos, pra girar o
  hash do chunk quando algum cache de navegador for envenenado. Incrementar =
  URL nova = cache podre ignorado.

## FASE 3 · Eventos (CAPI, `functions/api/tracker.js`)

- **`event_map` por domínio** traduz o nome NA SAÍDA (`Purchase → p`). No
  banco fica sempre o canônico; só a Meta recebe o espelhado.
- **`internal_only`**: etapas do funil (etapa01..16, cliques de presell) ficam
  SÓ no banco. Subir isso pro pixel enche a conta de eventos custom que
  poluem o painel e o aprendizado.
- **Paridade de EMQ**: enviar TODOS os parâmetros que o rastreio antigo
  enviava. A lista completa com hash SHA-256:

  | Parâmetro | Fonte | Nota |
  |---|---|---|
  | `em`, `ph`, `fn`, `ln` | captura/venda | telefone com DDI, nome minúsculo |
  | `external_id` | cookie `_bnd_eid` | |
  | `fbp`, `fbc` | cookies (sem hash) | `fbc` reconstruível do fbclid |
  | `client_ip_address`, `client_user_agent` | request (sem hash) | |
  | `zp`, `ct`, `st`, `country` | endereço da venda | **normalizar antes do hash**: minúsculo, sem acento, sem espaço ("São Paulo" e "sao paulo" têm que dar o mesmo hash) |
  | `ge` | inferência pelo primeiro nome | é INFERÊNCIA, não dado: declarar no código, calibrar com nomes reais de clientes, e o fallback é decisão de PÚBLICO (na Bluue 'm', produto masculino) |

- **Dedup navegador+servidor**: quando houver pixel no navegador, o MESMO id
  nos dois canais (`eventID` no fbq, `event_id` no CAPI).

## FASE 4 · Vendas (`workers/purchase-check/`)

Cron de 5min: busca vendas PAGAS no caixa → dedup no livro-caixa → casa pelo
`sck` (= session_id) → envia Purchase → registra resposta.

- **O checkout precisa levar `?sck=<session_id>`** na URL/params. É o fio que
  volta na venda e fecha o ciclo. Sem ele, casamento vira adivinhação por
  email.
- **Adapter por gateway**: a consulta de vendas é a única parte acoplada à
  plataforma (B4You pronto; outra plataforma = reescrever só `fetchPaidSales`).
- **Fuso**: confira `NOW()` do banco do gateway contra `date_update` de uma
  venda recém-paga ANTES de confiar em janelas de busca.
- **Venda sem casamento fica `unmatched` e NÃO sobe** (venda de funil alheio
  não pode sujar o pixel).
- Se o gateway devolver endereço, é daqui que saem `zp/ct/st/country` da
  Fase 3. Nada disso é gravado no nosso banco: hash, envia, descarta.

## FASE 5 · Teste A/B

Motor no porteiro (sorteio FNV-1a por sessão, cache 60s, falha aberta). Operação
completa na skill própria: **`teste-ab-bluue`** (criar, ler por R$/sessão,
conferir sorteio, encerrar). Duas regras que viajam junto:

- Texto testável precisa existir num **arquivo-base** lido pelo porteiro E pelo
  navegador (a troca acontece no HTML pré-renderizado; chave sem base = variante
  que nunca aparece, sem erro).
- Conferência do sorteio é **em par**: mesma sessão sempre na mesma variante E
  sessões diferentes se dividindo. Cada teste sozinho passa com um sorteio
  quebrado diferente.

## FASE 6 · Backup e BI

- Backup semanal D1 → R2 com **restauração testada** (backup sem restore
  provado não é backup).
- BI (Evidence) lê D1 + gateway. É da HOLDING, não da marca (domínio neutro), e
  atrás de Cloudflare Access (One-time PIN por email; o provedor precisa ser
  CRIADO, não vem por padrão). O guarda de host do BI muda JUNTO com o DNS.
- Dado individual de saúde NUNCA no BI público: exportação local sob demanda.

## FASE 7 · QA antes de tráfego

Bateria automatizada (modelo: `bluue/scripts/qa-virada.mjs`): roteamento por
domínio sem vazar redirect, sessão e crachás, nomes de evento por domínio,
scripts por domínio, dedup do ledger, sorteio em par, 404, painéis.

Se houver triagem/gate (médico, idade, elegibilidade): testar cada bloqueio E o
**teste de CONTROLE** (a combinação que NÃO pode bloquear). Sem o controle, um
código que bloqueia todo mundo passa em todos os testes de bloqueio.

O que a bateria não cobre e exige gente: compra real no cartão E no pix
(gerar o código, FECHAR a aba, pagar depois: é o caso que estrutura antiga
perde), e upsell abrindo a oferta certa.

## FASE 8 · A virada (domínio com anúncio ativo)

1. **Ensaio seco antes**: Purchase fictício com `test_event_code` no pixel de
   produção, com o nome espelhado e o `user_data` completo. Prova formato,
   token e tradução sem tocar em dado real.
2. **Paridade de EMQ provada** (Fase 3) ANTES de desligar o rastreio antigo.
3. **Anote o rollback antes de ir**: registro DNS atual, id, destino. Volta em
   2 minutos sem tocar em anúncio.
4. Um domínio vive em UM projeto Pages; a troca tem janela de certificado
   (segundos a minutos). Virar no vale de tráfego da operação.
5. A troca de DNS é atômica pro rastreio: o mesmo CNAME desliga o antigo e
   liga o novo. Sem janela de contagem dupla.
6. **Primeira hora olhando o livro-caixa**: primeira venda real tem que gravar
   o pixel certo + HTTP 200. Volume de eventos comparado à hora anterior.
7. Leitura limpa só com 24h completas. Até lá, NENHUMA outra variável muda
   (orçamento, criativo, página). Uma variável por vez.

---

## Os erros que esta stack já cometeu (detecte-os cedo)

| Erro | Como se manifesta | Antídoto |
|---|---|---|
| Comparar página por título/arquivo | rota "igual" com conteúdo diferente | renderizar e comparar texto |
| Categoria roteando (`role=funil`) | raiz servindo página errada | `root_route` explícito (fato) |
| 200-fallback + immutable | tela branca permanente pra alguns visitantes | 404 real + BUILD_TAG |
| Nome de evento canônico em conjunto treinado no custom | conversões zeram no Ads Manager | `event_map` por domínio |
| EMQ regredindo na troca de rastreador | nota cai, CPA sobe dias depois | paridade parâmetro a parâmetro contra o print |
| Venda da tela de obrigado | pix invisível, algoritmo aprende só cartão | worker no caixa + sck |
| Fuso do gateway | janelas curtas voltam vazias | comparar NOW() com venda recente |
| API da Meta paginada/filtro frouxo | inventário e contagens subestimados | paginar sempre, conferir status linha a linha |
| Chunk com nome "adv" | página em branco só pra quem tem adblock | nome interno neutro |
| Framer-motion em botão de entrada + AnimatePresence (React 19) | clique morto, funil congela | botão nativo, sem exit no switcher |
| Editar URL de anúncio ativo | revisão + aprendizado zerado | duplicar, nunca editar |
| Prova social com números divergentes | 4 números diferentes no mesmo funil | um número, o do anúncio |

## Referências

- Kit de arquivos: `_factorio/templates/cro-stack/` (este diretório)
- Implementação-modelo: `apps/br4nds/bluue` (sempre mais atual que o kit)
- Skill de A/B: `teste-ab-bluue`
- História completa das decisões: `apps/br4nds/_wiki/Holding/`
