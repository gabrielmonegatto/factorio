# 🏭 Filosofia da Fábrica — EternalL Factorio

> *"Não minta, não tenha vergonha de falar a real, Deus abençoe."*

---

## Princípio Central: A Fábrica é Simples por Fora, Poderosa por Dentro

Toda decisão arquitetural deve seguir uma regra: **um agente ou humano deve conseguir entender o estado de qualquer projeto em no máximo 2 consultas ao banco de dados.** Se precisar de mais, a arquitetura falhou.

---

## 🗂️ As Três Camadas de Dados

A operação é organizada em 3 camadas com papéis distintos e não intercambiáveis.

### 1. CONTENT — A Matéria-Prima e os Outputs

**O que é:** Tabela granular. Cada row é uma unidade de conteúdo (capítulo, devoção, sermão, chunk).

**Papel:** Armazenar o output de cada etapa de processamento no campo `pipeline_state` (JSONB).

**Regra de ouro:** O dado **É** o estado. Se o campo `translation_es` existe e tem `content`, a tradução está feita. Se não existe, está pendente. **Nenhum campo `status` redundante dentro do JSONB de output.**

**Exemplo de pipeline_state de um chunk:**
```json
{
  "translation_es": {
    "title": "DIOS JUSTIFICA AL IMPÍO",
    "content": "...",
    "model_used": "gemini-3.1-flash-lite",
    "revised_by": "llama-3.3-70b",
    "updated_at": "2026-06-22T20:29:51"
  },
  "narration_es": {
    "r2_url": "https://r2.eternall.../aog_03_es.mp3",
    "duration_s": 342,
    "voice": "pt-BR-Wavenet-A",
    "updated_at": "2026-06-23T10:00:00"
  }
}
```

> **Regra:** Scripts de processamento buscam chunks onde o campo de output **não existe** — nunca por um campo `status`.

---

### 2. INDEX — O Painel de Controle por Projeto

**O que é:** Tabela de catálogo. Cada row é um projeto/livro/fonte.

**Papel:** Centralizar o **estado agregado** de cada projeto em uma coluna JSONB (`pipeline`). É a fonte da verdade sobre *onde está* um projeto na fábrica.

**Regra de ouro:** Um agente consulta a INDEX e sabe tudo sobre um projeto sem precisar tocar na tabela CONTENT.

**Exemplo de pipeline na INDEX (livro):**
```json
{
  "total_units": 20,
  "mineracao": {
    "importacao": { "done": 20, "errors": 0, "status": "done" }
  },
  "i18n": {
    "es": {
      "traducao": { "done": 20, "errors": 0, "status": "done" },
      "revisao": { "done": 20, "errors": 0, "status": "done" }
    }
  },
  "produto": {
    "narracao_es": { "done": 0, "errors": 0, "status": "pending" },
    "publicacao": { "done": 0, "errors": 0, "status": "pending" }
  }
}
```

**Atualização:** Toda vez que um runner finaliza o processamento de um chunk, incrementa o contador correspondente na INDEX (`done += 1`). Se `done == total_units`, muda o `status` para `"done"` automaticamente.

**Reconciliação:** Um script leve roda periodicamente (e no boot do sistema) para recontar os chunks e garantir que os contadores na INDEX estão corretos — proteção contra crashes mid-process.

---

### 3. TASKS — O Dashboard da Fábrica (Visualização / KPIs)

**O que é:** Tabela de visibilidade da operação. É o painel de controle humano da fábrica.

**Papel:** Dar ao humano (e ao agente de supervisão) uma visão agregada e de alto nível de **todas as operações em andamento**. É o equivalente ao painel do Factorio mostrando throughput de cada linha de produção.

**Regra de ouro:** **1 task = 1 operação de alto nível.** Jamais 1 task por chunk.
734 capítulos de tradução = **1 task** chamada "Traduzir Morning and Evening (ES)".

**Exemplo de como fica o TASKS:**

| Task | Projeto | Etapa | Progresso | Status |
|------|---------|-------|-----------|--------|
| Traduzir All of Grace (ES) | All of Grace | i18n/es/traducao | 20/20 | ✅ Concluído |
| Traduzir Morning & Evening (ES) | Morning and Evening | i18n/es/traducao | 45/734 | 🔄 Em Progresso |
| Narrar All of Grace (ES) | All of Grace | produto/narracao_es | 0/20 | ⏳ Pendente |
| Importar E.M. Bounds | E.M. Bounds | mineracao/importacao | 5/7 | 🔄 Em Progresso |

**Atualização:** A row da TASKS é atualizada pelo mesmo evento que atualiza a INDEX. O runner finaliza um chunk → atualiza INDEX → atualiza progresso na TASKS. Automaticamente.

**O que NÃO vai mais na TASKS:**
- Tasks individuais por chunk (ex: `task_translate_rec_spurgeon_aog_03`)
- Tasks de renderização por sermão individual
- Qualquer task granular de execução interna

---

## 🔄 O Fluxo Correto de Uma Esteira

```
Runner Sequencial
       │
       ▼
Consulta CONTENT: "chunks do livro X onde pipeline_state->>'etapa' IS NULL"
       │
       ▼
Processa chunk (tradução, narração, etc.)
       │
       ▼
Salva output no JSONB do chunk (CONTENT)
       │
       ▼
Incrementa contador na INDEX: pipeline->'etapa'->>'done' += 1
       │
       ▼
Atualiza progresso na row da TASKS: "45/734 → 46/734"
       │
       ▼
Se done == total_units → marca INDEX e TASKS como "done"
       │
       ▼
Próximo chunk...
```

**Sem criar task por chunk. Sem tabela intermediária de fila. O runner é burro e simples.**

---

## 🚫 Anti-Padrões — O que NÃO Fazer

| Anti-Padrão | Por Quê é Ruim | Alternativa |
|-------------|----------------|-------------|
| Criar 1 task por chunk na TASKS | TASKS vira lixão ilegível com 1.349 rows | 1 task agregada por operação de alto nível |
| Campo `status` redundante dentro do JSONB de output | Estado duplicado gera inconsistência | O dado presente = feito. Ausente = pendente. |
| JOIN de 3+ tabelas pra saber onde um projeto está | Complexidade inviabiliza agentes | Consultar 1 JSONB na INDEX |
| Enfileirar tarefas antes de processar | Cria dependência de fila intermediária frágil | Runner itera diretamente nos chunks pendentes |
| Estado de execução na TASKS | TASKS é visualização, não controle de execução | Estado fica na INDEX (agregado) e CONTENT (granular) |

---

## 🧭 Mapa das Áreas e Etapas da Fábrica

Cada área da fábrica tem suas etapas mapeadas dentro do JSONB `pipeline` da INDEX:

```
mineracao/
  └── importacao
  └── estruturacao
  └── classificacao

inteligencia/
  └── indexacao
  └── vetorizacao

i18n/
  ├── es/
  │   ├── traducao
  │   └── revisao
  └── pt/
      ├── traducao
      └── revisao

produto/
  ├── narracao_es
  ├── narracao_pt
  ├── transcricao_es
  ├── transcricao_pt
  ├── capa
  └── publicacao

channels/
  ├── render_video
  ├── upload_youtube
  └── publicacao_social
```

---

## 🤖 Filosofia dos Agentes e Runners

- **Runners** são scripts Python simples e burros. Não tomam decisão — só processam o próximo chunk pendente e atualizam contadores.
- **Agentes** (LLMs) tomam decisão: "qual livro traduzir agora?", "qual área priorizar?", "o que está travado?".
- A **divisão clara** entre runner (execução) e agente (decisão) é fundamental para a saúde da fábrica.
- Nenhum runner cria tasks na TASKS. Nenhum agente executa processamento pesado diretamente.
- O agente de supervisão (Hermes no Discord) consulta a INDEX e a TASKS para ter visibilidade, e dispara runners quando necessário.

---

## 📅 Histórico de Decisões

| Data | Decisão | Motivação |
|------|---------|-----------|
| 2026-06-22 | Pipeline de tradução ES com Gemini 3.1 Flash Lite + Llama 3.3 70B | Free tier, fallback automático para capítulos grandes (>12k TPM) |
| 2026-06-22 | `responseSchema` no Gemini para garantir JSON válido | Capítulos com aspas internas quebravam o parse do JSON |
| 2026-06-22 | Runners sequenciais sem fila intermediária | Simplicidade, sem dependência de Trigger.dev para execução contínua |
| 2026-06-24 | Arquitetura de 3 camadas (CONTENT/INDEX/TASKS) definida | Complexidade crescente inviabilizava agentes e manutenção humana |
| 2026-06-24 | TASKS vira dashboard agregado (1 row por operação de alto nível) | 1.349 tasks granulares tornaram a tabela completamente inutilizável |
