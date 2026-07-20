# 🛠️ FERRAMENTAS E MODELOS — FÁBRICA ETERNALL
> Quais provedores usar, pra quê, e quanto custa

---

## 🧠 LLM (Raciocínio, Análise, Geração)

### PROVEDOR PRINCIPAL: OpenRouter

| Modelo | Uso | Custo / 1M tokens |
|---|---|---|
| DeepSeek V4 Flash | Agentes (80% do tempo) | ~$0.15 |
| Llama 8B | Workers leves, classificação | Grátis |
| GLM 5.2 | Workers médios (15%) | ~$0.10 |
| GPT-5.4 | Tarefas complexas (4%) | ~$10 |
| Claude Sonnet 4 | Emergência (1%) | ~$3 |

### ALTERNATIVAS GRÁTIS

| Provedor | Modelo | Uso | Limitação |
|---|---|---|---|
| Groq | Llama 4 Scout | Classificação rápida | Rate limit |
| Cloudflare Workers AI | Gemma 3 | Classificação leve | 10k req/dia |

---

## 🎙️ TTS / Narração de Áudio

### ATUAL: Kokoro (TTS open-source)
- **Onde roda:** VPS (CPU) ou RunPod CPU
- **Custo:** Grátis na VPS | ~$0.05/h no RunPod CPU
- **Idiomas:** EN, ES, PT
- **Modelo:** 82M parâmetros — leve, roda em CPU
- **Por que manter:** Já estamos usando em produção. Mudar de voz quebra consistência.

### Alternativas Cloud (futuro)

| Opção | Custo | Qualidade | Cloud? |
|---|---|---|---|
| OpenAI TTS (via OpenRouter) | $0.60/1M tokens | Excelente | ✅ |
| Edge-TTS (Microsoft) | Grátis | Boa | ✅ API |
| ElevenLabs | $5/mês (10min grátis) | Excelente | ✅ API |

---

## 🎤 Transcrição de Áudio

| Opção | Custo | Cloud? |
|---|---|---|
| **Groq Whisper** | **Grátis** ⭐ | ✅ Já temos |
| OpenAI Whisper | $0.006/min | ✅ |

**Recomendação:** Groq Whisper — grátis, rápido, funciona.

---

## 🖼️ Geração de Imagem

| Opção | Custo | Uso |
|---|---|---|
| **Cloudflare FLUX.1-schnell** | **Grátis** ⭐ | Thumbnails, backgrounds |
| OpenRouter (vários) | $0.001-0.01/img | Qualidade máxima |

---

## 🗄️ Armazenamento

| Serviço | Uso | Custo |
|---|---|---|
| **Cloudflare R2** | Assets, áudios, vídeos | 10GB grátis |
| **Teable** (Postgres) | Dados, tasks, schemas | Na VPS |
| **AgentMemory** | Memórias dos agentes | Na VPS |

---

## 🎬 Renderização de Vídeo

| Opção | Status | Custo |
|---|---|---|
| Remotion + RunPod (GPU) | 🟡 Pendente configurar | ~$0.20/h |
| Remotion local | ❌ Queremos eliminar | — |

---

## ⚡ Orquestração

| Ferramenta | Status |
|---|---|
| Trigger.dev (cloud) | ✅ Deployado — 10 tasks |
| Hermes Agent | ✅ Rodando na VPS |
| Docker Compose | ✅ 14 containers |

---

## 🔄 MAPA DE TRANSIÇÃO (Local → Cloud)

| Funcionalidade | Antes (Local/Python) | Agora (Cloud) |
|---|---|---|
| Orquestração | Prefect | **Trigger.dev** |
| Banco | Baserow | **Teable** |
| LLM | Chave única | **OpenRouter** (multi) |
| TTS | Kokoro local | Kokoro na VPS 🟡 |
| Transcrição | Whisper local | **Groq Whisper** |
| Imagens | DALL-E local | **Cloudflare FLUX** |
| Render | Remotion local | RunPod 🟡 |
| Agente | Script solto | **Hermes** 24/7 |