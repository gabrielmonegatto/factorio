# 🗺️ Mapa de Dados — onde cada coisa mora e por quê

> Escrito em 31/07/2026, depois da auditoria completa ([08_AUDITORIA_BANCO.md](08_AUDITORIA_BANCO.md)) e da caçada ao conteúdo dos livros.
> Responde: "onde isso vai morar?" e "por que não usar um banco só pra tudo?"

## 1. O achado: o conteúdo dos livros NÃO se perdeu

Houve um susto: a tabela `content_chunks` do Teable virou fantasma (tabela física dropada, só o metadata sobrou) e não está em backup nenhum. **Mas o conteúdo não estava mais lá.** Ele já tinha avançado para o Cloudflare.

**Onde está de verdade — D1 `mananciall-db`** (conta Eternall `dca6b1af...`, uuid `ddae6874-2058-4aa1-927e-0e7887e2cba6`, ~36 MB):

| Tabela | Linhas | O que é |
|---|---|---|
| `books` | 27 | 26 live + 1 draft. slug, título, autor, preço, capa, checkout |
| `chapters` | 2.201 | **`content_md` = o texto integral (~33 MB)** + `audio_url` |
| `collections` | 3 | agrupamentos |
| `entitlements` / `orders` / `leads` | 0 | comercial, ainda vazio |

**E os audiobooks — R2 `mananciall`, prefixo `audiobooks/`:** 9 livros, **1.214 capítulos narrados** (mp3) + 1.213 JSONs com `text` e `words` (timestamp por palavra). Servidos publicamente por `https://pub-cd23eb57aece4069a2df4818e6b9eed3.r2.dev` (verificado: HTTP 200, `audio/mpeg`).

### ⚠️ Buraco aberto (31/07): áudio pronto e invisível

Só **23 de 2.201** capítulos têm `chapters.audio_url` preenchido. Os outros 1.214 narrados existem no R2 mas o site não os serve. A narração foi paga e está invisível.

- Casamento verificado 1:1 nos 9 livros: 734/366/20/20/16/16/15/14/13 batem exato entre R2 e D1.
- Script pronto: `trigger/scripts/link_audiobooks_d1.py` (gera `link_audio.sql`, 1.214 UPDATEs idempotentes).
- Diferença de slug entre R2 e D1 já tratada no script: `morning-and-evening-daily-readings`→`morning-and-evening`, `faith-s-checkbook-of-decisive-testimony`→`faiths-checkbook`, `essentials-of-prayer`→`the-essentials-of-prayer`.
- **Pendente: gate humano** (rodar muda o site no ar).

## 2. Onde cada coisa mora hoje

| Casa | O que guarda | Quem lê |
|---|---|---|
| **Cloudflare D1 `mananciall-db`** | livros, capítulos, pedidos, leads | o site (Workers, no edge) |
| **Cloudflare D1 `br4nds`** | 3.448 criativos, players, insights do Meta | admin da Br4nds |
| **Cloudflare R2** | binários: áudio, vídeo, imagens, backups | site + fábrica |
| **Postgres/Teable (Hetzner)** | esteiras (`tasks`), mineração (36.7k vídeos), Bíblia (74k), catálogo bruto (545 obras), research (500) | a fábrica |
| **Supabase** | — | não usado (projeto pausado) |

## 3. A pergunta: por que não um banco só?

### O que cada um é bom (e ruim)

**Cloudflare D1 (SQLite no edge)**
- ✅ Mora colado nos Workers que servem o site: leitura rápida no mundo todo, sem servidor pra manter, barato.
- ❌ É SQLite: **um escritor por vez**, limite de tamanho por banco, sem JSONB, sem busca textual rica, consulta analítica pesada sofre.

**Postgres (VPS)**
- ✅ Banco de verdade: JSONB, busca textual, janelas, escrita concorrente e **claim atômico** (`FOR UPDATE SKIP LOCKED`) — que é o que uma fila de trabalho precisa pra dois operários nunca pegarem o mesmo job.
- ❌ Você mantém, vive numa VPS só, e do Worker é uma viagem pela internet a cada leitura.

### O veredito

**Não é fragmentação, é ferramenta certa pra cada trabalho.** A regra é uma só:

> **O dado mora perto de quem mais o lê.**

| Faixa | Onde | O que |
|---|---|---|
| **Entrega** (o cliente consome) | **Cloudflare D1 + R2** | livros, capítulos, áudio, criativos servidos, pedidos |
| **Fábrica** (constrói) | **Postgres** | fila/esteiras, mineração, pesquisa, catálogo bruto |

Fluxo: a **fábrica produz no Postgres → publica no D1 → o site serve do edge.**

Forçar tudo no D1 quebraria a fábrica (SQLite não faz claim atômico direito, e as tabelas de mineração já passam de 74k linhas e crescem). Forçar tudo no Postgres deixaria o site lento e penduraria o negócio numa VPS só.

## 4. Como VER os bancos do Cloudflare

Era o ponto fraco do D1, e deixou de ser: a Cloudflare **comprou a Outerbase** e embutiu no dashboard um explorador de dados (navegar/editar tabelas) e editor de query. A nuvem da Outerbase foi desligada em 15/10/2025 justamente porque virou parte da Cloudflare.

Opções, da mais simples à melhor:
1. **Dashboard da Cloudflare** — explorador de dados + console de query. Serve pro dia a dia, zero setup.
2. **Página de admin própria** — é o padrão que já funciona na casa: o admin de criativos da Br4nds lê o D1 e mostra do jeito que você quer. Melhor experiência, você controla.
3. **Ferramentas externas** — D1 Studio, DBCode (dentro do VS Code), d1-console.
4. **CLI** — `wrangler d1 execute <db> --remote --command "..."` (é o que a fábrica usa em automação).

## 5. Regras que ficam

- **Teable (schemas `bse*`)**: só API REST. Nada de DDL por SQL, nada de INSERT com `__id` inventado — foi isso que gerou os fantasmas e os 425 registros que a API não consegue escrever. `UPDATE` de valor por SQL é seguro.
- **D1**: mudança de schema por migration versionada no repo do app, nunca ad-hoc.
- **R2**: fonte da verdade dos binários. O banco guarda o *ponteiro* (URL), nunca o arquivo.
- **Publicar no D1 de produção = gate humano** (muda o que o cliente vê).
