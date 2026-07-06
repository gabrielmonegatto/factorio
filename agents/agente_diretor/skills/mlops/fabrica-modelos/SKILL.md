---
name: fabrica-modelos
description: "Model routing and cost hierarchy for EternalL Factory — choose the right LLM per task type, balancing agentic capability and token cost."
version: 1.0.0
author: Diretor de Operações / EternalL
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [model-routing, cost-optimization, llm, factory, eternalL, trigger-dev]
    related_skills: [agent-memory]
---

# 🧠 Fábrica Modelos — Model Routing para a EternalL

## Filosofia

**Modelo certo pra tarefa certa.** Não existe um modelo que serve pra tudo. O segredo da eficiência é:
- **Tarefas mecânicas → modelo minúsculo e barato**
- **Tarefas de decisão → modelo com capacidade proporcional à complexidade**
- **Custo importa** — "machuca o neném" se passar do ponto

## As Duas Categorias (REGRUA DE OURO)

**Modelo para AGENTES usarem** ≠ **Modelo para WORKERS usarem em tarefas específicas.**

Esta distinção é o coração da estratégia de modelos da Fábrica. Misturar as duas categorias é o erro mais comum e mais caro.

### 🤖 WORKERS (scripts, pipelines, tarefas específicas determinísticas)

Modelos **TINY** — baratos, rápidos, rodam em lote com concorrência alta.

| Modelo | Params | Pra que | Custo |
|--------|--------|---------|-------|
| **Llama 3.1 8B** 🏆 | 8B | Limpeza de texto, estruturação, formatação | Quase zero (via Groq/OpenRouter free tier) |
| Modelos <8B | <8B | Tarefas mecânicas (extrair data, contar, classificar) | Centavos |

**Worker profile:** Rápido, concorrência alta (8+ threads), não alucina em tarefa restrita, preserva o texto original.

**Caso de uso real (comprovado):** Pipeline de limpeza de acervos teológicos:
- 5.929 chunks processados, 0 pendências, 100% aproveitamento
- Textos brutos → Llama 3.1 8B → cola palavras hifenizadas, remove lixo de OCR/HTML, estrutura subtópicos
- Preserva linguagem original (inglês elisabetano de Spurgeon, grafia clássica em português)
- Concorrência: 8 threads simultâneas

**Worker pipeline flow:**
```
📥 Texto bruto minerado (HTML/PDF/OCR)
   → Chunking em blocos digeríveis
   → Llama 3.1 8B (via Groq ou OpenRouter)
     ├── Cola palavras hifenizadas (quebras de linha)
     ├── Remove lixo (cabeçalhos, botões de navegação, caracteres corrompidos)
     ├── Estrutura subtópicos e citações
     └── Preserva linguagem e tom original
   → Chunks → Capítulos → Pronto pra publicação
```

### 🧠 AGENTES (decisão, orquestração, raciocínio)

Modelos **MÉDIOS A GRANDES** — equilíbrio custo/capacidade com hierarquia definida.

| Prioridade | Modelo | Agentic Index | $/M tok (prompt/completion) | Uso |
|------------|--------|:------------:|:---------------------------:|-----|
| 🥇 **80%** | DeepSeek V4 Flash | 31.1 | $0.13/$0.27 | Tarefas de agente leves (resumir, extrair, classificar) |
| 🥇 **80%** | MiniMax-M3 | 35.4 | $0.30/$1.20 | Alternativa barata para tarefas leves |
| 🥈 **15%** | GLM 5.2 (Z.ai) | 43.1 | $1.40/$4.40 | Decisões, orquestração, análise — **melhor custo-benefício** |
| 🥈 **15%** | DeepSeek V4 Pro | 36.4 | $1.60/$3.13 | Alternativa para tarefas médias |
| 🥈 **15%** | Gemini 3.5 Flash | 37.4 | $1.50/$9.00 | Alternativa Google |
| 🥉 **4%** | GPT-5.4 | 41.1 | $2.50/$15 | Debug complexo, raciocínio multi-etapas |
| ⛔ **1%** | Claude Sonnet 4.6 | 40.8 | $3/$15 | Só quando os acima falharem |
| 🚫 **0.1%** | Claude Opus 4.x | 44+ | $5/$25+ | Emergência absoluta — "machuca o neném" |

### 🆓 Modelos Grátis (quando possível)

| Modelo | Via | Uso |
|--------|-----|-----|
| NVIDIA Nemotron 3 Ultra | OpenRouter (free) | Tarefas leves com reasoning |
| Poolside Laguna M.1 | OpenRouter (free) | Coding |
| Cohere North Mini Code | OpenRouter (free) | Coding leve |

## Como Decidir (Algoritmo de Roteamento)

```
1. A tarefa é um SCRIPT/PIPELINE (determinístico, repetitivo)?
   → WORKER: Llama 3.1 8B (ou menor)
   → Fim.

2. A tarefa é de AGENTE (precisa decidir, raciocinar, orquestrar)?
   → 2a. É simples? (resumir, extrair campo, classificar sentimento)
       → DeepSeek V4 Flash ($0.13/M tok)
       → Fim.
   → 2b. É média? (traduzir, estruturar, planejar workflow)
       → GLM 5.2 ($1.40/M tok) ← Custo-benefício rei
       → Se GLM falhar → Gemini 3.5 Flash ou DeepSeek V4 Pro
       → Fim.
   → 2c. É complexa? (debug multi-etapas, arquitetar sistema)
       → GPT-5.4 ($2.50/M tok)
       → Fim.
   → 2d. É crítica? (tudo falhou, precisa do melhor)
       → Claude Sonnet 4.6 ($3/$15) ou Opus 4.7 ($5/$25)
       → Fim.
```

## Como Implementar via OpenRouter MCP

O OpenRouter MCP (13 ferramentas) expõe `chat-send` que permite chamar QUALQUER modelo programaticamente:

```python
# Exemplo: roteador inteligente
def call_appropriate_model(task_type, prompt):
    model_map = {
        "worker": "meta-llama/llama-3.1-8b-instruct",
        "agent_leve": "deepseek/deepseek-v4-flash",
        "agent_medio": "z-ai/glm-5.2",
        "agent_pesado": "openai/gpt-5.4",
        "agent_critico": "anthropic/claude-sonnet-4.6",
    }
    model = model_map[task_type]
    # Chama via mcp_openrouter_chat_send tool
    return mcp_openrouter_chat_send(model=model, message=prompt)
```

O Hermes pode decidir dinamicamente qual modelo usar baseado na complexidade da instrução do usuário e no custo acumulado da sessão.

## Custo Diário Estimado

Rodando 24/7 com a distribuição 80-15-4-1:
- **~$2-5/dia** para operação normal de agentes
- **~$0.50-1/dia** para workers (quase de graça via Llama 8B)
- **Total: $3-6/dia** — a Fábrica inteira rodando por menos que um café

## Pitfalls

- ❌ **NÃO usar Claude como padrão.** É 40x mais caro que DeepSeek Flash e raramente necessário.
- ❌ **NÃO tratar todo modelo como agente.** Worker precisa de modelo TINY, rápido, concorrente.
- ❌ **NÃO ignorar free tiers.** Groq tem Llama 3.1 8B grátis, OpenRouter tem free models.
- ✅ **Sempre começar pelo mais barato.** Só escala se falhar.
- ✅ **Preservar custo-benefício do GLM 5.2** — agentic 43.1 por $1.40/M é o melhor negócio do mercado.
- ✅ **Workers rodam em lote com concorrência.** 8 threads paralelas é normal.

## Case Study Real

See `references/pipeline-limpeza-worker.md` for the concrete production pipeline that processed **5.929 chunks** with **100% success rate** using Llama 3.1 8B as the worker model.