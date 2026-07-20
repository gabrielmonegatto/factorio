# 🏭 Factorio — Manual Central da Fábrica EternalL

> *Última atualização: 01/07/2026*
> *Este documento é a ÚNICA fonte da verdade conceitual da Fábrica. Qualquer agente novo começa por aqui.*
> *Trigger.dev + Hermes + Teable. As 8 áreas. As 3 camadas. Desacoplamento radical.*

---

## 1. O Que é a Fábrica

A Fábrica (codinome **Factorio**) é o Business OS da **EternalL Holding**. Ela não produz o produto final — ela **produz agentes, automações e workflows** que rodam 24/7 construindo, escalando e operacionalizando os negócios do ecossistema.

**O Ecossistema:**
```
EternalL Holding
├── 🧠 _brain/          ← Conhecimento Destilado (Obsidian)
├── ⚙️ _factorio/       ← A FÁBRICA (Factorio — Business OS)
└── 🍎 apps/            ← OS FRUTOS
    ├── mananciall/      ← Desenvolvimento espiritual
    ├── markeologia/     ← Marketing + tecnologia
    └── entelekkia/      ← Desenvolvimento pessoal
```

---

## 2. Stack Tecnológica

| Camada | Tecnologia | Função |
|--------|-----------|--------|
| **Orquestração** | Trigger.dev (cloud) | Executa tasks em produção, schedules, retry |
| **Agentes/LLM** | OpenRouter multi-provider | LLM barato (DeepSeek, Gemini, etc) |
| **Agente Diretor** | Hermes (este) | Supervisão, orquestração, tomada de decisão macro |
| **Banco** | Teable (cloud, Postgres) | SSOT — tasks, content_index, content_chunks |
| **Runners** | Trigger.dev tasks (TypeScript) | Pipeline determinístico |
| **Scripts unitários** | Python avulso | Operações pontuais quando necessário |

**Regra:** Trigger.dev é o motor principal. Scripts Python unitários só pra operações isoladas. Hermes é o cérebro que decide e supervisiona.

---

## 3. As 8 Áreas da Fábrica

Cada área é uma **unidade autônoma** com propósito, fronteiras e indicadores claros. Desacoplamento radical entre elas.

| Área | Responsabilidade |
|------|-----------------|
| **🧠 Inteligência** | Market research, monitoramento de concorrentes, engenharia de funis, descoberta de fontes e tendências |
| **⛏️ Mineração** | ETL agnóstico — mapeia, extrai, limpa, estrutura e vetoriza conteúdo bruto da internet. SERVE A FÁBRICA TODA |
| **📦 Produto** | Desenvolvimento de produtos digitais (jornadas, app, livraria) |
| **📺 Channels** | Produção e distribuição de conteúdo (YouTube, Instagram, TikTok) |
| **📈 Growth** | Estratégias de crescimento, aquisição e retenção |
| **💻 Software** | Desenvolvimento de software interno e dos frutos (apps) |
| **🌐 i18n** | Internacionalização e localização cultural de conteúdo |
| **🔬 P&D** | Pesquisa e desenvolvimento de novas capacidades |

### Princípio: Desacoplamento Radical

Cada área funciona de forma **isolada**, ainda que todas sejam interdependentes. Cada workflow é composto por **tasks desacopladas**, ainda que interdependentes. Isso permite:

- Uma área falhar sem derrubar as outras
- Escalar áreas independentemente
- Substituir/atualizar workflows sem tocar nos outros
- Produtividade máxima por isolamento de responsabilidades

### A Esteira de Cada Área

Cada setor pode ter sua(s) própria(s) esteira(s) — uma tabela INDEX que centraliza o estado daquela área. **Não é regra fixa:** um setor pode ter uma ou mais esteiras. Exemplos atuais:

- **Channels:** `channels_index`, `channels_videos`, `channels_content_article_pipeline`
- **Produto:** `products_bible_journey`
- **Bíblia:** `bible_bible_*` (8 tabelas)
- **Inteligência:** `players_*`, `research_*`

A tabela **`tasks`** (base Eternall) dá a visão geral de todas as áreas.

---

## 4. As 3 Camadas de Dados (Coração da Fábrica)

```
CONTENT  →  INDEX  →  TASKS
(granular)  (agregado)  (dashboard)
```

### 4.1. CONTENT — A Matéria-Prima

**O que é:** Tabela granular. Cada linha é uma unidade de conteúdo (chunk, capítulo, sermão).

**Tabela real:** `content_chunks` (no Teable, base Eternall)

**Regra de ouro:** O dado **É** o estado. Se o campo de output existe, está feito. Se não existe, está pendente. **Sem campo `status` redundante dentro do JSONB.**

**Exemplo de pipeline_state:**
```json
{
  "translation_es": {
    "title": "DIOS JUSTIFICA AL IMPÍO",
    "content": "...",
    "model_used": "gemini-3.1-flash-lite",
    "updated_at": "2026-06-22T20:29:51"
  },
  "narration_es": {
    "r2_url": "https://r2.eternall.../aog_03_es.mp3",
    "duration_s": 342,
    "voice": "pt-BR-Wavenet-A"
  }
}
```

### 4.2. INDEX — O Painel de Controle por Projeto

**O que é:** Tabela de catálogo. Cada linha é um projeto/livro/fonte.

**Tabela real:** `content_index` (no Teable, base Eternall)

**Regra de ouro:** Um agente consulta a INDEX e sabe tudo sobre um projeto sem precisar tocar na CONTENT.

**Exemplo de pipeline na INDEX:**
```json
{
  "total_units": 20,
  "mineracao": { "importacao": { "done": 20, "errors": 0, "status": "done" } },
  "i18n": { "es": { "traducao": { "done": 20, "errors": 0, "status": "done" } } },
  "produto": { "narracao_es": { "done": 0, "errors": 0, "status": "pending" } }
}
```

### 4.3. TASKS — O Dashboard da Fábrica

**O que é:** Tabela de visibilidade da operação. É a SSOT (Single Source of Truth) da Fábrica.

**Tabela real:** `tasks` (no Teable, base Eternall)

**Regra de ouro:** 1 task = 1 operação de alto nível. NUNCA 1 task por chunk.

**Campos:** `Task ID`, `Brand`, `Project_Slug`, `area`, `Status`, `Projeto`, `Progresso`, `task`

**Exemplo:**

| Task | Projeto | Área | Progresso | Status |
|------|---------|------|-----------|--------|
| Traduzir All of Grace (ES) | All of Grace | i18n/es/traducao | 20/20 | ✅ Done |
| Narrar Morning & Evening (ES) | Morning and Evening | produto/narracao_es | 0/734 | ⏳ Pending |
| Importar E.M. Bounds | E.M. Bounds | mineracao/importacao | 5/7 | 🔄 In Progress |

---

## 5. Teable — A Única Fonte da Verdade

O **Teable** (Postgres + interface Airtable-like) é o banco central da Fábrica. Não existe discussão.

**Bases atuais:**
```
Teable Cloud (localhost:3000 / app.teable.ai)
├── Space: EternalL
│   ├── Base: Monegatto      ← Financeiro pessoal
│   ├── Base: Eternall       ← A FÁBRICA (~35 tabelas)
│   └── Base: Br4nds         ← Inteligência de marcas (outro escopo)
└── Space: Eternall
    └── Base: Base           ← Vazia
```

**Tabelas-chave da Base Eternall:**

| Tabela | Função |
|--------|--------|
| `tasks` | SSOT — visão geral de todas as áreas |
| `content_index` | INDEX — catálogo de projetos |
| `content_chunks` | CONTENT — chunks de conteúdo |
| `knowledge` | Base de conhecimento dos agentes |
| `agent_journal` | Histórico de decisões |
| `authors_index` | Índice de autores |
| `fonts_index` | Fontes de conteúdo |
| `channels_*` (4) | Pipeline de canais |
| `players_*` (2) | Inteligência competitiva |
| `research_*` (2) | Pesquisa |
| `bible_*` (8) | Acervo bíblico |
| `products_bible_journey` | Produto (jornada) |
| `org_chart` | Organograma da Fábrica |
| `agents`, `tools`, `skills`, `mcp`, `apis` | Infra dos agentes |

---

## 6. Mineração Agnóstica

A **Mineração** é a área mais estratégica por ser **agnóstica** — ela serve a fábrica como um todo:

```
INTERNET (fontes brutas)
    ↓
MINERAÇÃO (agnóstica)
    ├── Descobrir fontes
    ├── Mapear estrutura
    ├── Extrair conteúdo bruto
    ├── Limpar e normalizar
    ├── Chunkar
    └── Vetorizar
    ↓
    ├── → PRODUTO (jornadas, livros)
    ├── → CHANNELS (conteúdo, vídeos)
    ├── → P&D (inteligência procedural)
    ├── → SOFTWARE (dados pra apps)
    └── → etc (possibilidades infinitas)
```

**Arquitetura Universal (3 camadas):**
1. **Source Adapter** — Cada fonte (CCEL, Gutenberg, Archive.org) tem seu adaptador isolado. Saída normalizada.
2. **Catálogo Universal** (`content_index` + `content_chunks`) — Schema único com `metadata` JSONB pra absorver diferenças entre fontes.
3. **Fila de Autores** (`authors_index`) — Priorização por score (obras, relevância, audiência).

---

## 7. Runners vs Agentes vs Diretor

| Tipo | O que faz | Exemplo |
|------|-----------|---------|
| **Runner** (Trigger.dev task) | Execução determinística. Não decide nada. Só processa o próximo item e atualiza contadores. | "Traduzir próximo chunk pendente" |
| **Agente** (LLM) | Toma decisão. Decide qual livro traduzir, o que priorizar, o que está travado. | "Qual fonte minerar agora?" |
| **Diretor** (Hermes - este agente) | Orquestra + supervisiona. Cria roadmap. Monitora todas as esteiras. Reporta consolidado. | "Fábrica parou? Aciona runner X. Gargalo? Diagnostica." |

**Regra:** Nenhum runner cria tasks na TASKS. Nenhum agente executa processamento pesado. O Diretor não roda código de produção — ele decide, documenta e aciona.

---

## 8. Glossário Rápido

| Termo | Definição |
|-------|-----------|
| **Script** | Tarefeiro descartável. Roda, faz, morre |
| **Worker** | Funcionário que bate cartão e fica na estação. Loop infinito polling no banco |
| **Service/Daemon** | Worker rodando em segundo plano no sistema |
| **Agent** | Worker com cérebro LLM. Toma decisão |
| **Runner** | Task determinística no Trigger.dev |
| **Orchestrator** | O chefe que olha o quadro geral e coordena |
| **SSOT** | Single Source of Truth — a tabela `tasks` |
| **Pipeline State** | JSONB na CONTENT/INDEX — o dado **É** o estado |
| **Desacoplamento Radical** | Cada área isolada, workflows desacoplados, interdependência por estado no banco |
| **Esteira** | Pipeline de produção de uma área. Centralizada numa INDEX |

---

## 9. Anti-Padrões (o que NÃO fazer)

| Anti-Padrão | Problema | Alternativa |
|-------------|----------|-------------|
| 1 task por chunk na TASKS | TASKS vira lixão ilegível | 1 task agregada por operação de alto nível |
| Status redundante no JSONB | Estado duplicado gera inconsistência | Dado presente = feito. Ausente = pendente |
| JOIN de 3+ tabelas pra saber estado | Complexidade inviabiliza agentes | Consultar 1 JSONB na INDEX |
| Fila intermediária antes de processar | Dependência frágil | Runner itera direto nos pendentes |
| Runner cria tasks na TASKS | Mistura execução com visão | Runner atualiza CONTENT/INDEX → TASKS reflete |

---

## 10. Roadmap Pendente (Diretor)

- [ ] **AgentMemory** — Plugar todos os agentes numa camada de memória compartilhada (P2P sync)
- [ ] **Esteiras por área** — Cada uma das 8 áreas com sua INDEX centralizada
- [ ] **Dashboard/BI** — Visão consolidada de KPIs por setor, projeto, área
- [ ] **Pipeline state** — Verificar se `content_chunks` e `content_index` já têm os JSONB corretos
- [ ] **Mineração universal** — Source adapters pra Gutenberg, Archive.org, etc
- [ ] **Documentação viva** — Todo aprendizado documentado no Teable (`knowledge` + `agent_journal`)

---

> *"A Fábrica produz agentes, não o produto final. A esteira é a prioridade. Teable é a SSOT."*