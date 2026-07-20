# Teable — Base Eternall (Fábrica EternalL)

## Connection

**REST API:** http://localhost:3000  
**Token source:** `scratch/inspect_factorio.py` (look for `TEABLE_TOKEN`)  
**Alternative:** Postgres at localhost:42345 (but password auth may fail)

## Spaces

```
Space: EternalL (spc3R3vzE8F4hj8aq7v) — role: owner
├── Base: Monegatto (bseX6gpT5qn1T4Iq7Ph) — financeiro pessoal
├── Base: Eternall (bseWeczeNfCSaMlu2EC) — A FÁBRICA (~35 tabelas)
└── Base: Br4nds (bseyIWRa5nyTWMlNBpi) — inteligência de marcas

Space: Eternall (spcyUA1imPPbql7geNb)
└── Base: Base (bseFmVS893E3PYpyP4N) — vazia
```

## Base Eternall — Tabelas-Chave

### Core da Fábrica
| Tabela | ID | Função | Campos-chave |
|--------|----|--------|--------------|
| `tasks` | tblVzN1Eo8tfk7GX2CJ | SSOT — visão geral de todas as áreas | Task ID, Brand, Project_Slug, area, Status, Projeto, Progresso, task |
| `content_index` | tblD7Kxoc7gFTgEWoWo | Catálogo de projetos (INDEX) | Name, title, author, font_id, source_url, Brand, Project_Slug, discovered_at |
| `content_chunks` | tblFyPPXJTiynzBKFH2 | Chunks de conteúdo (CONTENT) | index_id, title, author, status, content, word_count |
| `knowledge` | tblFactoryKnowledge | Base de conhecimento dos agentes | title, category, tags, content, source, confidence |
| `agent_journal` | tblAgentJournal001 | Histórico de decisões | agent, type, summary, context |
| `authors_index` | tblzDDPI7RVpx2m2zQj | Índice de autores | Name, Notes, works, sources, status, birth_year, death_year, era |
| `fonts_index` | tblKMLYzdQG6EZw9fCl | Fontes de conteúdo | Name, Notes, URL, pipeline_status |
| `org_chart` | tblyFYKciHLDUtvhWcf | Organograma | Name, Description, workflows, tasks |

### Acervo Bíblico (8 tabelas)
| Tabela | Conteúdo |
|--------|----------|
| `bible_bible_books_index` | Livros da Bíblia |
| `bible_bible_verses_content` | Versículos |
| `bible_bible_commentaries_index` | Índice de comentários |
| `bible_bible_commentaries_content` | Comentários chunkados |
| `bible_bible_cross_references_index` | Referências cruzadas |
| `bible_bible_lexicon_index` | Léxico (índice) |
| `bible_bible_lexicon_content` | Léxico (definições) |
| `bible_bible_topics_index` | Tópicos |
| `bible_biblehub_index` | Scraping da BibleHub |

### Channels (4 tabelas)
| Tabela | Conteúdo |
|--------|----------|
| `channels_index` | Canais do YouTube |
| `channels_videos` | Vídeos dos canais |
| `channels_content_article_pipeline` | Pipeline de artigos |
| `channels_content_articles` | Artigos de conteúdo |

### Inteligência (2 tabelas)
| Tabela | Conteúdo |
|--------|----------|
| `players_index` | Players de mercado |
| `players_criativos` | Criativos dos players |
| `players_pages` | Páginas dos players |

### Pesquisa (2 tabelas)
| Tabela | Conteúdo |
|--------|----------|
| `research_index` | Índice de pesquisa |
| `research_content` | Conteúdo pesquisado |

### Produto
| Tabela | Conteúdo |
|--------|----------|
| `products_bible_journey` | Jornada bíblica |

### Infra
| Tabela | Conteúdo |
|--------|----------|
| `agents` | Definições de agentes |
| `tools` | Ferramentas |
| `skills` | Skills dos agentes |
| `mcp` | Servidores MCP |
| `apis` | Registro de APIs |
| `content_vectors` | Vetores de conteúdo |

## API Examples

```bash
# List spaces
curl -s http://localhost:3000/api/space

# List bases in space
curl -s http://localhost:3000/api/space/spc3R3vzE8F4hj8aq7v/base

# List tables in base
curl -s http://localhost:3000/api/base/bseWeczeNfCSaMlu2EC/table

# List fields in table
curl -s http://localhost:3000/api/table/tblVzN1Eo8tfk7GX2CJ/field
```

Add header: `Authorization: Bearer {token}`