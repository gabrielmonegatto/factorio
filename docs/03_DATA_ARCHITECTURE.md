# 🗄️ DATA ARCHITECTURE — ONDE VIVE CADA DADO

> Regra de bolso: **cada dado tem UMA casa, escolhida pela natureza dele.**
> Duplicação e sync bidirecional são proibidos — são fábricas de conflito e drift.

---

## 1. O mapa das casas

| Natureza do dado | Casa | Exemplos | Quem acessa |
|---|---|---|---|
| **Narrativa de negócio** | **Outline** | Wiki das marcas, briefings, análises, decisões, relatórios de rotina, docs de idealização/design de templates | Gabriel pela UI; Claude via API REST |
| **Tabular operacional** | **Teable** | `tasks`, `content_index`, `content_chunks`, esteiras por área, inteligência competitiva | Esteiras e sessões via API |
| **Código executável** | **Git** | Skills, scripts, tasks trigger.dev, templates de site, schemas, estes docs | Claude Code (commits auditáveis) |
| **Produto em produção** | **D1** (Cloudflare) | `domain_config`, `quizzes`, `data_tracker`, `campaign_insights` | Workers/Pages em runtime |
| **Assets binários** | **R2** (produção) / **MinIO** (anexos do Outline) | Áudios narrados, vídeos renderizados, imagens | Esteiras (upload), produtos (serve) |
| **Credenciais** | `_factorio/.env` | Tokens, chaves | NUNCA commitar; CRLF — usar `tr -d '\r'` no shell |

**Fato técnico (verificado no docker-compose em 18/07/2026):** o Outline tem Postgres PRÓPRIO (`outline_db`, pg16, porta 54322), separado do Postgres do Teable (`factorio_teable_db`, pg15, porta 42345). As duas instâncias Outline (holding + br4nds) usam o mesmo `outline_db`. Anexos no MinIO.

## 2. A decisão do "banco único" — os 3 caminhos avaliados

O desejo original era "tudo num banco só, estilo Notion". Avaliação honesta dos caminhos:

### Caminho A — Banco único físico (tudo no Outline OU tudo no Teable) ❌

- **Tudo no Outline**: Outline é banco de *documentos* (páginas, coleções, revisões). Não tem queries por campo, filtros, JSONB, contadores. Os 69k versículos e 36k rows de YouTube virariam páginas de texto inertes — **as esteiras morrem**. Inviável.
- **Tudo no Teable**: o inverso — documentos longos virariam texto dentro de células. Sem hierarquia, sem links ricos, leitura/edição humana péssima. Gabriel não leria o negócio ali. Inviável.
- **Veredito**: perverter a natureza de um dos dois lados quebra ou a máquina ou o humano.

### Caminho B — Tudo em git markdown (Outline morre ou vira espelho) ⚠️

- **Prós**: máquina adora (arquivos nativos pro Claude), versionamento e diff de graça, zero serviço extra.
- **Contras**: a UX humana piora muito (sem UI bonita, sem mobile confortável, edição exige editor+commit). Outline como "espelho read-only" adiciona um sync unidirecional — mais uma peça, com drift garantido.
- **Veredito**: tecnicamente limpo, mas sacrifica exatamente o que Gabriel pediu — ler e gerir o negócio numa interface tipo Notion.

### Caminho C — Casa única POR NATUREZA + Outline como interface humana ✅ (ESCOLHIDO)

- O insight: **até o Notion, por dentro, é vários bancos** (Postgres + S3 + warehouse). A sensação de "tudo num lugar" vem da INTERFACE, não do banco físico.
- Narrativa → Outline (canônico). Tabular → Teable (canônico). Executável → git (canônico). Cada pergunta tem um lugar óbvio de resposta; nada existe em dois lugares.
- **Trade-offs assumidos**: (1) Claude acessa Outline via API em vez de arquivo local — ok, é uma API REST boa; (2) exige disciplina anti-duplicação — coberta pelas regras abaixo; (3) `outline_db` entra na rotina de backup.

## 3. Regras anti-duplicação

1. **Skill vive em git.** No Outline existe só a página-catálogo (lista com 1 linha por skill). Nunca copiar conteúdo de skill pra lá.
2. **Estado operacional vive no Teable.** Relatório no Outline pode CITAR números ("45/734 traduzidos"), nunca ser a fonte deles.
3. **Decisão registrada uma vez**: decisões de negócio → Outline; decisões técnicas de código → no próprio repo (docs/commit). Referenciar, não copiar.
4. Se um dado parece precisar de duas casas, a modelagem está errada — parar e redesenhar.

## 4. Migração da wiki atual (`apps/br4nds/_wiki` → Outline)

- A wiki markdown da Br4nds **venceu como processo** e agora ganha a casa definitiva: importada pro **Outline Br4nds** via API (Outline importa markdown nativamente).
- Gradual, coleção por coleção, começando por `Holding/`. Durante a transição, a página importada no Outline passa a ser a canônica e o arquivo markdown ganha banner "MIGRADO → link".
- A frente Bluue/tracking continua usando `_wiki/` até a migração da coleção dela — sem quebrar o fluxo de quem está operando lá. (Timing na Fase 2 do roadmap; coordenar com a outra frente antes.)
- `_brain/` (Obsidian pessoal) permanece pessoal — o que for da fábrica é destilado pros lugares certos, o resto não se toca.

## 5. Acesso do Claude a cada casa

| Casa | Como |
|---|---|
| Outline | API REST (`/api/documents.*`, `/api/collections.*`) com API key — via scripts ou MCP dedicado (config na Fase 1) |
| Teable | API REST oficial (token corporativo) — nunca SQL bruto no Postgres, exceto manutenção de emergência |
| Git | Nativo (Claude Code) |
| D1 | `wrangler d1` / API Cloudflare (escopo da frente Br4nds) |
| R2/MinIO | S3 API (scripts já existentes em `_factorio/`) |

## 6. Backups (rotina da Fase 2)

| O quê | Como | Cadência |
|---|---|---|
| `outline_db` (pg16) | `pg_dump` → R2 | Semanal |
| `teable_db` (pg15) | `pg_dump` → R2 | Semanal |
| D1 | Export JSON → R2 (Time Travel cobre 30d como primeira linha) | Semanal |
| Git | Push para remote | Contínuo |
