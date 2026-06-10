# 🏭 Factorio (Ecossistema EternalL)
**Arquitetura "Jardim do Éden" (Baseada em workflows com trigger.dev)**

Este ecossistema foi desenhado seguindo a filosofia de automação industrial. A regra de ouro é a modularidade estrita: **nenhum workflow sabe da existência do outro, e todos compartilham os mesmos agentes e dados.**

---

## 🏗️ Taxonomia do Sistema

### 1. ⚙️ `trigger/` (O Motor de Execução)
Onde a roda gira. Workflows em TypeScript orquestrados pelo trigger.dev (nuvem).
*   **`tasks/`**: Tasks isoladas — cada arquivo é um workflow.
*   Gatilhos: webhooks, schedules (cron), ou filas.

### 2. 🤖 `agents/` (O RH da Fábrica)
Agentes Python autônomos para trabalho pesado (mineração, ETL, IA).

### 3. 🔌 `mcp_universal/` (Conectores)
Servidor MCP que expõe ferramentas (Baserow, banco, LLM) para os agentes.

### 4. 🎬 `remotion/` (Renderização)
Motor de vídeo baseado em React.

---

## 🚀 Como Iniciar

```bash
# 1. Instalar dependências
cd _factorio
npm install

# 2. Fazer login no trigger.dev cloud
npm run login

# 3. Iniciar dev mode (hot reload local)
npm run dev
```

### Primeira vez?

1. Crie uma conta em [cloud.trigger.dev](https://cloud.trigger.dev)
2. Crie um projeto e copie o `project ref`
3. Cole no `trigger.config.ts` no campo `project`
4. Rode `npm run dev`

---

## 📋 Tasks Atuais

| Task | ID | Trigger | Descrição |
|---|---|---|---|
| Ping | `ping` | Manual/webhook | Teste de conexão |
| Pesquisar Foreplay | `pesquisar-foreplay` | Webhook | Busca anúncios por termo |
| Relatório Diário | `relatorio-diario` | Cron (08:00) | Relatório automático diário |
| **Pixel Perfect** | `pixel-perfect` | Manual/webhook | Clona qualquer URL como projeto Astro (extração Playwright + QA visual) |
| Pixel Perfect QA | `pixel-perfect-qa` | Manual | Roda diff visual após reconstrução Astro |

---

## 🐳 Infraestrutura (Docker)

```bash
docker compose up -d
```

Levanta: Postgres, Redis, Baserow, NocoDB, MCP Universal, Agent Workers.