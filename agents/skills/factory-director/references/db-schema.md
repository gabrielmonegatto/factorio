# Database Schema — Fábrica EternalL

## Conexão
```
URL: postgresql://teable:teable_secret_password@localhost:42345/teable
```

## Schemas

### Schema de Conteúdo: `bseWeczeNfCSaMlu2EC`

#### content_index (CATALOG) — `"bseWeczeNfCSaMlu2EC"."tblD7Kxoc7gFTgEWoWo"`
Catálogo de livros/projetos. Cada row = um livro.

Colunas importantes:
- `__id` — ID único (ex: `recsxt0CLYAIgh8zlwz`)
- `Name` — Nome do livro
- `author` — Autor
- `pipeline_status` — `pending` | `em_producao` | `concluido`
- `pipeline_state` — JSONB com estado agregado:
  ```json
  {
    "total_units": 20,
    "published_en": {"done": 20, "status": "done"},
    "translation_es": {"done": 0, "status": "pending"}
  }
  ```
- `has_content` — BOOLEAN
- `complete_content` — BOOLEAN

#### mineration_content (CONTENT) — `"bseWeczeNfCSaMlu2EC"."tblFyPPXJTiynzBKFH2"`
Conteúdo granular (capítulos, devocionais). Cada row = uma unidade.

Colunas importantes:
- `__id` — ID único
- `index_id` — FK para content_index.__id
- `title` — Título da unidade
- `content` — Texto do conteúdo
- `author` — Autor
- `book_name` — Nome do livro
- `status` — `backlog` | `pending` | `concluido`
- `metadata` — JSON com metadados extras
- `pipeline_state` — JSONB com estado do pipeline:
  ```json
  {
    "narration_en": {"status": "done", "r2_url": "...", "updated_at": "..."},
    "transcript_en": {"status": "done", "...": "..."},
    "published_en": {"status": "done", "path": "...", "updated_at": "..."}
  }
  ```

### Schema de Workflow: `bseWeczeNfCSaMlu2EC`

#### tasks — `"bseWeczeNfCSaMlu2EC"."tblVzN1Eo8tfk7GX2CJ"`
Tabela de tarefas operacionais.

Colunas:
- `__id` — ID único (ex: `task_spurgeon_xxx`, `task_transcribe_xxx`)
- `Task_ID` — Título descritivo
- `Instruction` — Conteúdo/instrução
- `Status` — `Pendente` | `Em Processamento` | `Concluído` | `Erro`
- `Projeto` — JSON array com project ID
- `Task` — Slug da task (`narrate-audio`, `transcribe-audio`, `translate-content`, `publish`)
- `Area` — `channels` | `produto` | `i18n`
- `resultado` — Resultado/URL do output
- `Logs` — Logs de execução
- `__created_time`, `__last_modified_time` — Timestamps

#### projects — `"bseWeczeNfCSaMlu2EC"."tblalvN0Db5K9S7Hrb6"`
Mapeamento de projetos.

---

## NOVA PIPELINE: `public.mananciall_sermon_pipeline`

Pipeline de sermões (Spurgeon, etc.). Cada row = um sermão.

Colunas:
- `id` (uuid) — PK
- `title` (text) — Título do sermão
- `author` (text) — Autor (ex: "Charles Spurgeon")
- `status` (text) — `pending` | `processing` | `done` | `erro`
- `content` (text) — Conteúdo limpo (AI-cleaned)
- `raw_content` (text) — Conteúdo bruto original
- `word_count` (integer) — Palavras do conteúdo limpo
- `audio_status` (text) — `pending` | `processing` | `completed` | `erro`
- `full_audio_path` (text) — Caminho do áudio gerado
- `transcription_status` (text) — `pending` | `processing` | `completed` | `erro`
- `transcription_path` (text) — Caminho da transcrição
- `narration_status` (text) — `pending` | `processing` | `completed` | `failed`
- `narration_path` (text) — Caminho da narração
- `ai_cleaning_status` (text) — `pending` | `processing` | `completed` | `failed`
- `youtube_title`, `introduction_youtube`, `cta_narration_script` — CTA/YT fields
- `plane_issue_id` (text) — ID de issue externa
- `created_at`, `updated_at` — Timestamps

---

## PIPELINE DE ARTIGOS: `bible.article_pipeline`

Pipeline de artigos bíblicos (biografias, panoramas).

Colunas importantes:
- `id` (uuid) — PK
- `source_ref` (varchar) — URL/ref original
- `source_type` (varchar) — `ray_stedman_book`, `BIOGRAPHY`, etc.
- `status` (varchar) — `PENDING` | `PROCESSING` | `READY` | `REVIEW` | `ERROR` | `DONE`
- `current_agent` (varchar) — Agente atual processando
- `draft_title` (text) — Título do rascunho
- `draft_content` (text) — Conteúdo do artigo
- `score_theology`, `score_tech`, `score_nexus` (integer) — Scores de qualidade
- `feedback_*` (text) — Feedback dos revisores
- `blueprint` (jsonb) — Metadados da blueprint (categoria, fonte taxonômica)

---

## PIPELINE DE JORNADA: `mananciall.journey_production`

Jornada de leitura bíblica diária.

Colunas:
- `day_number` (integer) — Dia da jornada (1-30+)
- `book_name` (text) — Livro bíblico
- `reference` (text) — Referência (ex: "João 1")
- `daily_theme` (text) — Tema do dia
- `status` (text) — `pending` | `done`
- `content_intro`, `content_explanation`, `content_devotional` (text) — Conteúdo a ser gerado
- `created_at`, `updated_at` — Timestamps

---

## VOICE FACTORY: `factorio.*`

### `factorio.vf_channels`
Canais do YouTube gerenciados pela voice factory.
- `id`, `name`, `niche`, `language`, `youtube_channel_id`, `status`, `brand`

### `factorio.vf_episodes`
Episódios produzidos.
- `id`, `topic_id`, `channel_id`, `script`, `seo`, `assets_path`, `output_path`, `youtube_video_id`

### `factorio.vf_topic_backlog`
Backlog de tópicos para produção de vídeo.
- `id`, `channel_id`, `title`, `keywords`, `priority`, `status`, `briefing`

---

## FLUXO DAS PIPELINES

1. **Pipeline Antiga (Teable):** Catálogo → `enqueue_pipeline_tasks.py` cria tasks → `universalCron` (Trigger.dev) dispatches tasks → narrator/transcriber/translator/publisher
2. **Pipeline Nova (mananciall_sermon):** Itens já importados, todos em `status='pending'` — sem consumidor atualmente
3. **Artigos (bible.article_pipeline):** Artigos gerados por IA, status `READY` aguardando publicação
4. **Journey:** Conteúdo a ser gerado por agente