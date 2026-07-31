# 🔍 Auditoria do Banco (Teable/Postgres) — 31/07/2026

> Levantamento completo de TODAS as bases e tabelas: o que existe, o que tem dado real, o que é casca vazia, o que está quebrado. Feito antes de qualquer decisão de arquitetura.
> Servidor: Postgres 15.18 no container `factorio_teable_db` (Hetzner), 117 MB. Teable em `https://db.markeologia.com.br`.

## Método

- Inventário via `table_meta` + `information_schema` (todas as bases).
- "Com dado" = linhas que têm ao menos uma coluna de usuário não-nula e não-vazia (ignora colunas `__*` de metadata do Teable).
- Drift = colunas físicas no Postgres que NÃO estão registradas como campo do Teable (invisíveis na API REST).

## 1. Mapa por cluster (só o que tem dado real)

### Bíblia — ~74.000 linhas (o maior acervo)
| Tabela | Linhas c/ dado |
|---|---|
| `bible_biblehub_index` | 69.190 |
| `bible_bible_verses_content` | 1.001 |
| `bible_bible_commentaries_content` | 1.001 |
| `bible_bible_commentaries_index` | 1.001 |
| `bible_bible_lexicon_content` | 1.001 |
| `bible_bible_lexicon_index` | 1.001 |
| `bible_bible_books_index` | 133 |
| `bible_bible_topics_index` | 55 |
| `bible_journey` | 30 |
| `bible_bible_cross_references_index` | 1 |

### Mineração de canais — ~37.700 linhas
| Tabela | Linhas c/ dado | O que é |
|---|---|---|
| `channels_videos` | 36.736 | vídeos minerados de canais terceiros (views, engajamento, `mining_status`) |
| `channels_content_articles` | 652 | artigos derivados |
| `channels_content_article_pipeline` | 315 | pipeline dos artigos |
| `channels_index` | 50 | canais monitorados (ex: Luciano Subirá 1,89M, The Theologist 25,7k) |

### Conteúdo / livros
| Tabela | Linhas c/ dado | Situação |
|---|---|---|
| `content_index` | 545 | catálogo de obras, com `source_url` (ccel.org) + `pipeline_state` rico (categoria, capa, descrição) |
| `authors_index` | 419 | autores |
| `fonts_index` | 15 | fontes de mineração |
| `content_chunks` | 💀 | **tabela física não existe** (ver §2) |
| `content_vectors` | 0 | casca vazia (5 linhas, nenhuma com dado) |

### Research / CRO
| Tabela | Linhas c/ dado |
|---|---|
| `research_index` | 499 (artigos de marketing crawleados, ex: marketingexperiments) |
| `research_content` | 19 |
| `research_fonts` | 1 |

### Players (concorrentes) — DUPLICADO em 3 bases
| Base | `players_index` | `players_pages` | `players_criativos` |
|---|---|---|---|
| Eternall | 8 | 14 | 46 |
| Br4nds | 8 | 253 | 1.375 |
| Zoac | 1 | 23 | — |

### Br4nds (base própria)
| Tabela | Linhas c/ dado |
|---|---|
| `br4nds_criativos` | 3.448 (bate exato com o D1 do admin de criativos) |
| `players_criativos` | 1.375 |
| `players_pages` | 253 |
| `br4nds_index` | 3 |

### Operação da fábrica — quase tudo VAZIO
| Tabela | Linhas | C/ dado | Situação |
|---|---|---|---|
| `tasks` | 425 | 425 | painel AGREGADO (não é fila), alimentado por `reconcile` que está quebrado |
| `org_chart` | 10 | 10 | só nomes de área |
| `agent_journal` | 5 | 5 | |
| `agents` | 1 | 1 | 1 agente cadastrado |
| `tools` | 3 | 2 | |
| `skills` | 3 | **0** | casca |
| `cycles` | 3 | **0** | casca |
| `products_index` | 3 | **0** | casca |
| `knowledge` | 0 | 0 | vazia |
| `mcp` | 💀 | | tabela física não existe |

### Monegatto (base pessoal) — 100% VAZIA
5 tabelas (patrimônio, orçamento, lançamentos, balanço, wishlist), 3 linhas cada, **zero com dado**. Template nunca usado.

## 2. O que está quebrado

### Fantasmas (metadata sem tabela física)
| Tabela | Views | Efeito |
|---|---|---|
| `mcp` | 0 → **1 (consertado 31/07)** | Sem view padrão, o endpoint que lista as tabelas da base estourava 404 e **a base inteira não abria na UI**. Consertado criando uma view (nada foi apagado). Clicar nela ainda dá erro. |
| `content_chunks` | 2 | Não derruba a base, mas quebra ao abrir. Era a tabela de trabalho do pipeline de livros. |

### Drift de colunas (existem no Postgres, invisíveis na API REST)
| Tabela | Colunas órfãs |
|---|---|
| `content_index` | `pipeline_state` ← **estado de TODOS os 545 livros mora aqui, e a API não vê** |
| `tasks` | `resultado`, `background_image`, `preacher_image`, `bgm_audio` |

Só 2 tabelas com drift: o estrago foi **limitado**, não sistêmico.

### Causa raiz de tudo
Escrita por **SQL bruto dentro dos schemas do Teable** (`bse*`). O Teable mantém uma camada de metadata (tabelas/campos/views); SQL direto não a atualiza. Resultado: tabela dropada vira fantasma, coluna criada vira invisível. Ambos os incidentes (`mcp` em ~11/jul, `content_chunks` em ~01/jul) são o mesmo pecado.

## 3. Sobre o `content_chunks` perdido

- **Não está em backup nenhum**: nem no dump de 22/jul (VPS antiga), nem no de 25/jul (R2), nem na VPS antiga (que segue viva em `187.127.44.153`, 28 dias de uptime). Foi dropada antes de 22/jul.
- **MAS o produto sobreviveu no R2** (`audiobooks/`): **9 livros · 1.214 capítulos narrados (mp3) · 1.213 JSONs com `text` + `words` (timestamp por palavra)**.

| Livro | Capítulos |
|---|---|
| morning-and-evening-daily-readings | 734 |
| faith-s-checkbook-of-decisive-testimony | 366 |
| all-of-grace | 20 |
| power-through-prayer | 20 |
| the-necessity-of-prayer / the-reality-of-prayer | 16 cada |
| essentials-of-prayer | 15 |
| purpose-in-prayer | 14 |
| the-weapon-of-prayer | 13 |

Ou seja: perdeu-se o **estado intermediário**, não o trabalho. E o resto do catálogo é re-minerável, porque `content_index` guarda `source_url` dos 545.

## 4. Conclusões

1. **O acervo é sólido e vale muito**: ~74k de Bíblia, ~37k de mineração de canais, 545 obras catalogadas, 500 de research, 3.448 criativos. Isso é o ativo.
2. **A camada OPERACIONAL não existe de fato.** As tabelas da fábrica (`skills`, `cycles`, `products_index`, `knowledge`) estão vazias, e `tasks` é um painel agregado defasado, não uma fila. Não há SSOT de produção: o estado real do vídeo vive em arquivo no R2, e o dos livros numa coluna invisível (`pipeline_state`).
3. **O Teable está saudável** (2 fantasmas, 2 tabelas com drift, resto íntegro). O problema foi disciplina de escrita, não a ferramenta.
4. **Bases duplicadas**: `players_*` existe em Eternall, Br4nds e Zoac. Precisa decidir qual é a fonte.

## 5. Regra que fica (para nunca repetir)

- Dentro dos schemas `bse*` do Teable: **só API REST**. Nunca `CREATE`/`DROP`/`ALTER` por SQL.
- Leitura por SQL é segura (não corrompe metadata) e é o caminho rápido pra relatório.
- Estado de máquina de alta escrita (fila) não deve morar em tabela do Teable sem decisão explícita: a API não tem claim atômico (`FOR UPDATE SKIP LOCKED`), então com mais de um operário há risco de trabalho duplicado.
