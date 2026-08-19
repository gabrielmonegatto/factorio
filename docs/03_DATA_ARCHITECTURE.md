# 🗄️ DATA ARCHITECTURE — ONDE VIVE CADA DADO

> Regra de bolso: **cada dado tem UMA casa, escolhida pela natureza dele.**
> Duplicação e sync bidirecional são proibidos — são fábricas de conflito e drift.
> **Reescrito em 19/08/2026** (unificação: Teable aposentado, tudo que é máquina vai pro D1).
> A versão anterior (Outline narrativa + Teable tabular) está no histórico do git.

---

## 1. O mapa das casas

| Natureza do dado | Casa | Exemplos | Quem acessa |
|---|---|---|---|
| **Gestão da fábrica** (curadoria humana) | **Notion** | Áreas, Roadmap, Esteiras, Indicadores, Tasks, Biblioteca Mananciall, Referências de Editoras | Gabriel pela UI; Claude via API (`tools/notion/`) |
| **Estado da máquina** | **D1** (Cloudflare) | Filas de esteira, texto minerado, produto/vendas, intel de mercado, snapshots de BI, tracking | Esteiras e sessões via API HTTP do D1; produtos em runtime |
| **Código executável** | **Git** | Skills, scripts, esteiras, templates de site, schemas, estes docs | Claude Code (commits auditáveis) |
| **Assets binários e arquivo morto** | **R2** | Áudios, vídeos, capas, snapshots crus de mineração, backups, arquivo do que foi aposentado | Esteiras (upload), produtos (serve) |
| **Credenciais** | `_factorio/.env` | Tokens, chaves | NUNCA commitar; CRLF — usar `tr -d '\r'` no shell |

### Os bancos D1 (conta Eternall `dca6b1af…`)

| Banco | Papel | Frente dona |
|---|---|---|
| `mananciall-db` | Produto: livros, capítulos, orders, entitlements, leads, scans | Productz |
| `mananciall-mining` | Fila e texto bruto minerado (`works`, `chapters`, `runs`) | Mineração |
| `eternall-intel` | Inteligência: canais, vídeos, players, criativos, páginas, autores, pesquisa | Int. de Mercado |
| `mananciallbible` | App de estudo bíblico | Productz |
| `br4nds` | Tracking/experimentos do cliente | frente Br4nds (fora da fábrica) |
| `lifesystem` | Entelekkia (vida) | fora da fábrica |

**Limites do D1 que importam** (medidos, não temidos): 10 GB por banco, ~100 KB por statement (fatiar UPDATE de capítulo grande), escrita serializada por banco, sem JOIN entre bancos diferentes. Nosso maior banco tem ~107 MB. Time Travel cobre 30 dias; backup semanal pro R2 cobre o resto.

## 2. A regra-mãe: máquina × humano

```
Máquina escreve na MÁQUINA (D1/R2/git).
Notion é PLANO DE CONTROLE humano + vitrine.
Sync é de MÃO ÚNICA (máquina → Notion), exceto os campos onde o Gabriel manda.
```

Campos do Gabriel (a máquina nunca sobrescreve): Estado editorial, Prioridade, Lançamento, Coleções, Destaque, Nota, Preço. Campos da máquina (ele não edita): Slug, Capítulos, Faixas, Tamanho, Página, Sincronizado.

**Por que o Notion é descartável por design:** ele é vitrine, não fonte. O sistema próprio que vem no fim de 2026 (padrão `bi.br4nds.com.br`) lê do D1, nunca do Notion. Migrar = trocar a vitrine, não mover dado.

**Limites do Notion que decidem o desenho:** ~3 req/s sem endpoint de lote (1.000 linhas ≈ 10 min), relation trunca em 25 na resposta, view/layout não existe na API, a API não move página de pai. Por isso: volume nunca vai pro Notion.

## 3. Regras anti-duplicação

1. **Skill vive em git.** No Notion existe no máximo a página-catálogo (1 linha por skill). Nunca copiar conteúdo pra lá.
2. **Estado operacional vive no D1.** Página do Notion pode CITAR números ("24 obras mineradas"), nunca ser a fonte deles.
3. **Decisão registrada uma vez**: decisão de negócio → Notion; decisão técnica → doc/ADR no repo. Referenciar, não copiar.
4. Se um dado parece precisar de duas casas, a modelagem está errada — parar e redesenhar.
5. **Binário nunca em banco.** Vai pro R2; a tabela guarda a chave.

## 4. Escolhendo a casa de um dado novo (árvore de decisão)

```
É credencial? ................................. .env (e só)
É binário (áudio/vídeo/imagem/PDF)? ........... R2 (chave no D1)
É código ou SOP? .............................. git
Muda por rodada de esteira / tem milhares de linhas? ... D1
Humano cura por semana e precisa ver bonito? ... Notion (e só o resumo)
```

Empate entre D1 e Notion resolve assim: **quem escreve mais vezes por semana, a máquina ou o humano?** Máquina → D1 com espelho opcional no Notion.

## 5. Acesso do Claude a cada casa

| Casa | Como |
|---|---|
| D1 | API HTTP do D1 com **parâmetro vinculado** (texto grande sem escapar aspas) ou `wrangler d1 execute`. Gotcha: `--command` quebra com SQL multi-linha (achatar); precisa de `CLOUDFLARE_ACCOUNT_ID` no env (há 4 contas na credencial) |
| Notion | API REST via `tools/notion/*.mjs` (lê `NOTION_TOKEN` do `.env`). A integração só enxerga páginas compartilhadas com ela |
| Git | Nativo (Claude Code) |
| R2 | `wrangler r2 object put/get` ou S3 API (`R2_*` no `.env`) |

## 6. Backups

| O quê | Como | Cadência |
|---|---|---|
| D1 (todos os bancos) | `scripts/backup/d1_backup.mjs` → R2 `eternall-archives/d1/` | Semanal (+ Time Travel 30d nativo) |
| Notion (bancos de gestão) | `scripts/backup/notion_backup.mjs` → R2 `eternall-archives/notion/` | Semanal |
| Git | Push para remote | Contínuo |
| R2 | É a casa do arquivo; versionamento por prefixo datado | — |

## 7. O que foi aposentado (e por quê)

| Peça | Morte | Motivo |
|---|---|---|
| **Outline** (wiki self-hosted) | 23/07/2026 | Fricção humana: sem database-in-doc, sem embed. Notion tomou o lugar |
| **Teable** (banco tabular self-hosted) | 19/08/2026 | Virou peça avulsa: D1 tomou o estado, Notion tomou a curadoria. Sobrava um Postgres pra cuidar (cert vencido, `tasks` quebrada na API, paginação travando em 1.001 linhas). Migração completa: `17_UNIFICACAO_DE_DADOS.md` |
| **trigger.dev** | 19/08/2026 | Nada em produção usava: render é systemd, agendador é cron, esteiras são script + fila no D1. Substituto futuro, se precisar: Cloudflare Workflows/Queues |
| **AgentMemory / Hermes** | 07/2026 | Modelo de agentes da era 1.0 (ver `05_LEGACY_TRANSITION.md`) |

Padrão que se repete nas quatro: **serviço self-hosted que duplica papel de algo gerenciado vira dívida.** Antes de subir container novo, perguntar qual casa existente já resolve.
