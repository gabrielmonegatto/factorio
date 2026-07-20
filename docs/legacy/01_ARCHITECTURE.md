# 🏗️ ARQUITETURA — FÁBRICA ETERNALL
> Stack, 3 camadas de dados, visão geral
> Baseado em: factorio_philosophy.md + MANUAL_DA_FABRICA.md

---

## 1. STACK TECNOLÓGICA

```
┌─────────────────────────────────────────────┐
│           HERMES AGENT (Diretor)             │
│         Orquestração + Gateway + Crons       │
├─────────────────────────────────────────────┤
│           TRIGGER.DEV (Cloud)                │
│        10 tasks • Pipeline • Schedules       │
├─────────────────────────────────────────────┤
│  TEABLE DB    │  AGENTMEMORY   │  R2         │
│  (Postgres)   │  (Memórias)    │  (Assets)   │
├─────────────────────────────────────────────┤
│  OPENROUTER │ GROQ │ CLOUDFLARE │ YOUTUBE    │
│  LLM/TTS    │ STT  │  Imagem    │   API      │
├─────────────────────────────────────────────┤
│              DOCKER (VPS)                    │
│      14 containers • factorio_network        │
└─────────────────────────────────────────────┘
```

## 2. AS 3 CAMADAS DE DADOS (Filosofia)

```
┌──────────────────────────────────────────────────┐
│  🎯 TASKS (Dashboard da Fábrica)                  │
│  O quê: operações de alto nível                   │
│  Onde: Teable (tblVzN1Eo8tfk7GX2CJ)              │
│  Ex: "Narrar Áudio (ES) — Spurgeon Vol.30"       │
│  425 registros ativos                             │
├──────────────────────────────────────────────────┤
│  📇 INDEX (Catálogo de Projetos)                  │
│  O quê: registros agregados por projeto/autor     │
│  Onde: Teable (content_index)                     │
│  Ex: "Spurgeon's Sermons Volume 30: 1884"        │
├──────────────────────────────────────────────────┤
│  📦 CONTENT (Matéria-Prima)                       │
│  O quê: dados brutos, chunks, versículos           │
│  Onde: Teable (content_chunks, bible_verses)      │
│  Ex: "Sermão #1845 — texto original + chunks"    │
│  ~69k rows (bible_verses) + 36k rows (YouTube)   │
└──────────────────────────────────────────────────┘
```

### Regras de Ouro
1. **Dado É o Estado** — sem campo `status` redundante no JSONB. O estado está no dado.
2. **Desacoplamento entre áreas** — Mineração não sabe o que Canais vai fazer com o conteúdo.
3. **1 task = 1 operação de alto nível** — nunca 1 task por chunk.
4. **Nenhum runner cria tasks** — a task existe antes do runner começar.
5. **Pipeline state é JSONB inline** — não polui o schema com colunas de estado.

## 3. ÁREAS DA FÁBRICA (8 setores)

| Área | Função |
|---|---|
| **Inteligência** | Discovery, briefing, análise de mercado |
| **Mineração** | Extrair, limpar, catalogar conteúdo |
| **Produto** | Transformar conteúdo em produto digital |
| **Canais** | YouTube, podcasts, distribuição |
| **Growth** | Crescimento, aquisição, tráfego |
| **Software** | Infra, ferramentas, automação |
| **i18n** | Internacionalização, localização |
| **P&D** | Pesquisa, prototipação, inovação |

## 4. WORKERS vs SCRIPTS (Paradigma)

### ❌ Modelo Antigo (Monolito)
```
spurgeon_master_pipeline.py
  ├── 1. Coleta dados
  ├── 2. Limpa conteúdo    ← Se falha aqui, tudo para
  ├── 3. Narra áudio
  └── 4. Publica           ← Pipeline linear frágil
```

### ✅ Modelo Novo (Workers Autônomos)
```
factory_collector.py (loop infinito)
  └── Polling no banco → pega próximo job → executa → atualiza
    ↻ Repete

factory_narrator.py (loop infinito)
  └── Polling no banco → pega áudio pendente → narra → atualiza
    ↻ Repete
```

**Worker é inteligente e auto-gerenciado.** O banco é o "Quadro de Avisos".