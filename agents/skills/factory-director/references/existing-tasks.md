# Existing Tasks & Runners

## Trigger.dev Tasks (execução na nuvem)

| Task ID | Função |
|---------|--------|
| `mananciall/channels/yt_en_treasures_spurgeon/narrate-audio` | Gera áudio TTS de um texto |
| `mananciall/channels/yt_en_treasures_spurgeon/transcribe-audio` | Transcreve áudio via Whisper |
| `mananciall/produto/books/translate-content` | Traduz conteúdo (EN → ES) |
| `mananciall/produto/books/publish` | Publica conteúdo como Markdown no Mananciapp |
| `mananciall/produto/audiobooks/migrate` | Migra audiobooks locais pro R2 |
| `mananciall/software/factorio/universal-cron` | Cron universal (roda a cada 15min) |

## Python Scripts (tools/)

| Script | Função |
|--------|--------|
| `auto_cure_tasks.py` | Destrava tasks presas (reset de status) |
| `enqueue_pipeline_tasks.py` | Enfileira novos livros na pipeline |
| `get_pending_tasks.py` | Busca tasks pendentes no banco |
| `narrator_db.py` | Gera áudio e salva no banco |
| `transcribe_db.py` | Transcreve áudio e salva no banco |
| `translate_revision_db.py` | Traduz e revisa conteúdo |
| `publish_all.ts` | Publica todos os livros completos |
| `migrate_local_to_r2.py` | Sobe arquivos locais pro Cloudflare R2 |

## Arquitetura de Dados (3 Camadas)

```
CONTENT (mineration_content)
  ├── Dado granular (capítulos, devocionais)
  ├── pipeline_state JSONB → "se campo existe, está feito"
  └── status: backlog | pending | concluido

INDEX (content_index / CATALOG)
  ├── Catálogo de projetos/livros
  ├── pipeline_state JSONB → estado agregado
  ├── pipeline_status: pending | em_producao | concluido
  └── 1 consulta = saber tudo sobre um projeto

TASKS (tasks)
  ├── Painel de controle operacional
  ├── 1 row = 1 operação de alto nível
  └── Status: Pendente | Em Processamento | Concluído | Erro
```

## Fluxo de uma Esteira

```
Runner consulta CONTENT → encontra chunk pendente
    → processa (traduz, narra, transcreve)
    → salva output no pipeline_state
    → incrementa contador na INDEX
    → atualiza progresso na TASKS
    → se done == total → marca como concluído
```

## Anti-Padrões (NÃO FAZER)
- Criar 1 task por chunk na TASKS (vira lixão)
- Campo status redundante dentro do JSONB
- JOIN de 3+ tabelas (1 consulta na INDEX resolve)
- Fila intermediária entre runners (runner itera direto)