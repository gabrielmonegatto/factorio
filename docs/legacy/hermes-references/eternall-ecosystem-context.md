# EternalL Ecossistema — Mapa de Contexto

> Atualizado: 01/07/2026 — após faxina de documentação e alinhamento de stack.

## Estrutura Raiz (do README.md + correções do CEO)

```
EternalL/                    ← Holding Eternal Legacy
├── _brain/                  ← Conhecimento Destilado (Obsidian, _brain/projectz/_factorio/ etc)
├── _factorio/               ← AS RAÍZES — O Business OS (Factorio)
│   ├── agents/              ← Definições de agentes (diretor, minerador, builder)
│   ├── trigger/tasks/       ← Workflows em produção no Trigger.dev (TypeScript)
│   ├── skills/              ← Conhecimento dos agentes
│   └── tools/               ← Ferramentas da fábrica (docker, remotion, mcp)
├── apps/                    ← OS FRUTOS (Produtos Finais)
│   ├── entelekkia/          ← Desenvolvimento pessoal
│   ├── markeologia/         ← Marketing + tecnologia
│   ├── mananciall/          ← Desenvolvimento espiritual (matriz)
│   └── br4nds/              ← Marcas/games (bluue, tonaface, etc)
├── scratch/                 ← Scripts exploratórios e de inspeção
└── repos/                   ← Repositórios clonados (referências, templates)
```

**Documentação da Fábrica concentrada em:** `_brain/projectz/_factorio/`
- `⭐ MANUAL_DA_FABRICA.md` — Central (leia primeiro)
- `MANUAL_DA_FABRICA.md` — Original (Trigger.dev+TS+Teable)
- `factorio_philosophy.md` — 3 camadas CONTENT/INDEX/TASKS
- `⭐ FACTORIO_PROJECT.md` — 8 áreas + checklists
- `⭐ SETORES_FABRICA.md` — Cartas dos setores
- `⭐ MINERACAO_UNIVERSAL.md` — Arquitetura de mineração
- `⭐ OKR's.md` — OKRs
- `_archive/` — Documentos obsoletos/não-fábrica
- `tools_ref/` — Docs de terceiros (DeepAgents, Firecrawl, LangChain)

## Marcos (Apps)

| Marca | Foco | Stack |
|-------|------|-------|
| **Mananciall** | Desenvolvimento espiritual. Tudo começa e termina aqui. | Next.js + Supabase + Stripe |
| **Markeologia** | Desenvolvimento de negócios (marketing + tecnologia) | Next.js + Supabase |
| **Entelekkia** | Desenvolvimento pessoal | Next.js + Supabase |
| **Br4nds** | Marcas digitais (bluue, tonaface, milagrosa) | Vercel + Firebase + Supabase |

## Fábrica (Factorio) — Stack Real

| Camada | Tecnologia | Função |
|--------|-----------|--------|
| **Orquestração** | Trigger.dev (TypeScript) | Motor principal — tasks, schedules, retry |
| **Banco** | Teable (Postgres local:42345) | SSOT única — base Eternall |
| **LLM** | OpenRouter multi-provider | DeepSeek, Gemini, etc |
| **Agente Diretor** | Hermes | Supervisão, orquestração, decisão |
| **Runners unitários** | Python avulso | Só pra operações isoladas |

## Teable — SSOT

Space: **EternalL** → Base: **Eternall** (~35 tabelas)

| Tabela | Função |
|--------|--------|
| `tasks` | SSOT — visão geral de todas as 8 áreas |
| `content_index` | INDEX — catálogo de projetos |
| `content_chunks` | CONTENT — chunks de conteúdo |
| `knowledge` | Base de conhecimento dos agentes |
| `agent_journal` | Histórico de decisões |

## As 8 Áreas

| Área | Propósito |
|------|-----------|
| Inteligência | Market research, monitoramento, funis |
| Mineração | ETL agnóstico — serve toda a fábrica |
| Produto | Jornadas, livros, devocionais |
| Channels | YouTube, Instagram, TikTok |
| Growth | Crescimento e aquisição |
| Software | Desenvolvimento técnico |
| i18n | Internacionalização e localização cultural |
| P&D | Pesquisa e desenvolvimento |

## AgentMemory (Conectado)\n\nCamada de memória compartilhada entre todos os agentes da Fábrica.\n\n- **REST API:** http://localhost:3120/agentmemory/health\n- **Viewer:** http://localhost:3122/\n- **Secret:** `factorio_secret`\n- **MCP Tools:** 53 (memory_save, memory_recall, memory_smart_search, memory_patterns, memory_graph_query, memory_team_share, memory_consolidate, etc)\n- **Versão:** 0.9.27 (Docker, com persistência de dependências ONNX)\n- **MCP Server no Hermes:** Configurado no profile `diretor` (mcp_servers.agentmemory)\n\nQualquer agente da Fábrica que se conectar ao mesmo AgentMemory compartilha o pool de memórias — decisões, estado, alertas e aprendizados ficam disponíveis para todos.\n\n### Como configurar novos agentes\n\n```env\nAGENTMEMORY_URL=http://localhost:3120\nAGENTMEMORY_SECRET=factorio_secret\n```\n\nNo Hermes, adicionar ao `config.yaml` (seção `mcp_servers`):\n\n```yaml\nmcp_servers:\n  agentmemory:\n    url: http://localhost:3120/agentmemory/mcp\n    headers:\n      Authorization: Bearer factorio_secret\n    timeout: 180\n    connect_timeout: 30\n```\n\n### Protocolo de memória\n\nVer skill `agent-memory` para o protocolo completo de o que/quando/como salvar memórias.\n\nTags usadas: `fabrica:estado`, `fabrica:decisao`, `fabrica:alerta`, `fabrica:config`, `fabrica:aprendizado`, `area:*`
