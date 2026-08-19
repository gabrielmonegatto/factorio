# tools/notion — kit da wiki empresarial no Notion

Scripts que construíram (e reconstroem) o sistema Notion do Gabriel. A estrutura é
**código reproduzível**: pra migrar pro workspace pago (Marqueologia), roda os builders
de novo apontando pra outra página-mãe e reimporta os dados. Relations nascem certas,
sem o problema de "relation quebra entre workspaces".

**Auth:** todos leem `NOTION_TOKEN` do `_factorio/.env` (integração "factorio").
**Rodar:** `node <script>.mjs` (Node 18+, sem dependências).

## Ferramenta viva (uso recorrente)

| Script | O que faz |
|---|---|
| `notion-instanciar-playbook.mjs "<Marca>" ["<Playbook>"]` | **A linha de montagem.** Clona um checklist-mestre do banco Playbooks: cria projeto "Playbook — Marca" + N tasks com hierarquia/áreas em Tasks do Business System. Agentes marcam progresso nas tasks via API; o mestre fica intacto. |
| `notion-map.mjs` | Mapeia a árvore de páginas/bancos (recursa em colunas/toggles/callouts). Editar `ROOTS` no fim. |
| `notion-dump.mjs` | Dump de conteúdo de bancos pra JSON (leitura, zero escrita). |
| `notion-fabrica.mjs` | **A fábrica (19/08/2026).** Página 🏭 Fábrica + upgrade do esboço "Mananciall Roadmap" do Gabriel → db `Áreas` (blueprint + prompt de frente na página de cada área) + dbs `Roadmap`/`Esteiras`/`Indicadores` + relation `Área` no Tasks + seeds. Fonte: `docs/16_BLUEPRINT_AREAS.md`. Idempotente via `notion-fabrica-ids.json`. |

## Dojo (treino pessoal — executado em 11/08/2026)

`notion-dojo.mjs` + `notion-dojo-fontes.mjs` — dicionário de golpes/drills de boxe e kickboxing
com sistema de faixas, dentro do Life System. Reprodutível: apaga a página e roda de novo.

- Banco **Faixas** (5: Branca→Preta) = a progressão. Cada faixa exige Técnicas + Drills + um teste de passagem.
  Lógica copiada do IKS do Shane Fazen (FIGHTTIPS/MAGNVS): a faixa se GANHA por critério, não por tempo.
- Banco **Técnicas** (53) = o dicionário. Mecânica, erros comuns, vídeo, checkbox `Dominado`.
- Banco **Drills** (25) = como se repete. Ligado às Técnicas que treina.
- `% Domínio` na Faixa é **rollup `percent_checked`** sobre o checkbox `Dominado` das Técnicas —
  por isso existe checkbox além do select `Domínio`: rollup de select não calcula percentual.
- Conteúdo minerado de `Desktop\trainingcenter\{treino-boxe\boxe.db, treino-chutes\chutes.db}`
  (1.482 + 1.069 vídeos) + os `docs\curriculo_*.md`. Fontes escritas verificadas foram pro banco Recursos.

## Builders (histórico executado em 23-24/07/2026 — reusáveis pra migração)

Ordem de execução original:

1. `notion-build.mjs` — 3 bancos relacionais (Unidades/Projetos/Tasks) + board BLUUE
2. `notion-migrate.mjs` — fusão Business System + Life System velhos na espinha
3. `notion-trevvo.mjs` — Trevvo 1.0: 17 bancos → 3 (Contas/Lançamentos/Categorias, saldo automático)
4. `notion-metas.mjs` — fusão Polaris + Metas → banco Metas (59, hierarquia, estados)
5. `notion-recursos.mjs` — biblioteca Recursos (Bloom) ligada às Maestrias
6. `notion-bs.mjs` — split das instâncias: bancos [B.S.] na página Business System, unificados viram [L.S.]
7. `notion-playbooks.mjs` — Playbooks (57 etapas) + Experimentos (ICE) a partir da página modeling
8. `notion-cleanup.mjs` — deleta bancos legados fundidos (lixeira). ⚠️ Deleção em massa: rodar só com aval do Gabriel.

Os `notion-*-ids.json` guardam os IDs criados por cada builder (os scripts seguintes leem deles).

## IDs canônicos (workspace pessoal "Monegatto")

⚠️ **A página-cofre "Newsystem" NÃO EXISTE MAIS** (404 desde ~08/2026). Gabriel arrastou os bancos
pra fora e apagou, como estava planejado. Metas e Recursos hoje moram **inline dentro da página
Life System** (`b9e16270-1b1c-463c-95bd-d7778ed94ab7`, filha do workspace) — o parent deles é
`block_id` (callout dentro de coluna), não `page_id`. Builder novo deve criar página própria
sob Life System / Business System, nunca sob o cofre.

- Página Business System: `33d6bf27-9f65-4043-8a5d-c53fe0b241a3`
- Página Life System: `b9e16270-1b1c-463c-95bd-d7778ed94ab7`
- Dojo: página `3b9f06f1-0ce3-819e-9521-c7ab292d7acf` · Faixas `3b9f06f1-0ce3-818e-891b-c3157799f8c0` · Técnicas `3b9f06f1-0ce3-817d-8eb2-fb1eeff7ff31` · Drills `3b9f06f1-0ce3-810a-8047-eb0cb57de9e9`
- Unidades `3a6f06f1-0ce3-816d-84ea-d6ce6ddeb89f` · Projetos `3a7f06f1-0ce3-81d2-9dd9-ddad8d16109c` · Tasks `3a7f06f1-0ce3-81cd-8696-cc002c44f430` (Business)
- Projetos [L.S.] `3a6f06f1-0ce3-81c7-bb20-c668d4d85c38` · Tasks [L.S.] `3a6f06f1-0ce3-817a-9068-de47ac0b3b11`
- Metas `3a7f06f1-0ce3-8153-a258-ebbff106eab9` · Recursos `3a7f06f1-0ce3-8177-950e-e703ebb71da3`
- Trevvo: Contas `3a7f06f1-0ce3-81c8-9414-c18cc156554f` · Lançamentos `3a7f06f1-0ce3-8159-9ef2-dfc787cd4cc7` · Categorias `3a7f06f1-0ce3-81a6-831c-f8f43e0fedce`
- Playbooks `3aaf06f1-0ce3-81f0-b2dd-cf47760bd1b2` · Experimentos `3abf06f1-0ce3-8175-b137-ee2c573837d8`
- 🏭 Fábrica (19/08/2026, sob Business System): hub `3c1f06f1-0ce3-8117-87df-d894ffd804f9` · Áreas `3c1f06f1-0ce3-8076-908b-fbcb7b67294c` (ex "Mananciall Roadmap") · Roadmap `3c1f06f1-0ce3-81ff-bdba-f04376322409` · Esteiras `3c1f06f1-0ce3-8167-989b-d56a4207f266` · Indicadores `3c1f06f1-0ce3-8196-9da9-e8c5895d2e4d` · Tasks ganhou relation `Área`. Linhas de área em `notion-fabrica-ids.json`.

## Gotchas da API (aprendidos na marra)

- Rate limit ~3 req/s, sem endpoint de lote: 1 request por linha (46 linhas ≈ 30s).
- Query pagina em 100; **array de relation trunca em 25 na RESPOSTA** (não é dado faltando — conferir pelo outro lado da relation).
- **Fórmula é sintaxe v1**: `if()` aninhado; `ifs()` não existe; `or()/and()` aceitam SÓ 2 args (aninhar).
- Property `status` não pode ser criada via API (usar `select`).
- Property `people` só aceita usuários do workspace (time externo → `multi_select`).
- **View/layout não existe na API** (view não migra; Kanban/agrupamento é manual na UI).
- **A API NÃO MOVE página/banco de pai** — mover é só arrastando na UI.
- Self-relation: criar o banco primeiro, adicionar a relation via PATCH depois (não dá na criação).
- Back-relation nasce "Related to X (Prop)" — renomear via PATCH no banco alvo.
- Ícone padrão dos bancos: `https://www.notion.so/icons/database_green.svg` (regra do Gabriel: nome limpo, sem emoji).

## Convenções do sistema

- **Banco = fonte única** (mora numa página-cofre); páginas temáticas são vitrines de linked views.
- Fundir bancos quando as linhas são a mesma coisa em estados diferentes; separar quando a natureza difere (Projetos ≠ Tasks).
- Instâncias separadas Business × Life (compartilhamento é por banco, nunca por linha).
- Régua de ferramenta: máquina escreve toda hora/milhares de linhas → Teable/Postgres; binário → R2; curadoria humana semanal → Notion.
