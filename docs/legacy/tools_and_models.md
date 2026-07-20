# 🛠️ FERRAMENTAS E MODELOS — FÁBRICA ETERNALL
> Documento de referência: quais ferramentas/modelos usamos, onde, e quanto custam
> Atualizado: 08/07/2026

---

## 1. PROVEDORES DE LLM (Raciocínio, Análise, Geração)

### OpenRouter — ✅ PRINCIPAL
| Modelo | Uso | Custo |
|---|---|---|
| DeepSeek V4 Flash | Agentes (Diretor, 80%) | ~$0.15/M tokens |
| GPT-5.4 | Tarefas complexas (4%) | ~$10/M tokens |
| Claude Sonnet 4 | Emergência (1%) | ~$3/M tokens |
| GLM 5.2 | Workers (15%) | ~$0.10/M tokens |
| Llama 8B | Workers leves | Grátis |

### Groq — ✅ TRANSCRIÇÃO + LLM RÁPIDO
| Modelo | Uso | Custo |
|---|---|---|
| Whisper large-v3 | Transcrição de áudio | **Grátis** (rate limited) |
| Llama 4 Scout | Classificação rápida | Grátis |

### Cloudflare Workers AI — ✅ IMAGEM + BACKGROUND
| Modelo | Uso | Custo |
|---|---|---|
| FLUX.1-schnell | Geração de imagens/thumbs | **Grátis** (10k/dia) |
| Gemma 3 | Classificação leve | Grátis |

---

## 2. TTS / NARRAÇÃO DE ÁUDIO 🎙️

### Opções Cloud Disponíveis

| Opção | Custo | Qualidade | Idiomas | Cloud? |
|---|---|---|---|---|
| **OpenAI TTS** (via OpenRouter) | $0.60/1M tokens ⭐ | Excelente | EN, ES, PT, + | ✅ Sim |
| **Edge-TTS** (Microsoft) | **Grátis** ✅ | Boa | EN, ES, PT, + | ✅ API HTTP |
| **ElevenLabs** | $5/mês (free: 10min) | Excelente | EN, ES, PT, + | ✅ API |
| **Google Cloud TTS** | $0.004/1k chars | Excelente | 220+ vozes | ✅ API |
| **OpenAI GPT Audio Mini** | $0.60/1M tokens | Excelente | EN | ✅ OpenRouter |
| **Kokoro** (open-source) | Grátis (precisa GPU) | Boa | EN, ES, PT | ❌ Local (ou HF) |

### Recomendação
```
1ª opção: OpenAI TTS via OpenRouter (já temos a chave, super barato)
2ª opção: Edge-TTS API (grátis, bom para testes)
3ª opção: ElevenLabs (qualidade máxima, pago)
```

---

## 3. TRANSCRIÇÃO 🎤

| Opção | Custo | Qualidade | Cloud? |
|---|---|---|---|
| **Groq Whisper** | **Grátis** ⭐ | Excelente | ✅ Sim |
| OpenAI Whisper API | $0.006/min | Excelente | ✅ Sim |
| Faster-Whisper (local) | Grátis | Boa | ❌ Local |

**Recomendação:** Groq Whisper — grátis, rápido, cloud. ✅

---

## 4. GERAÇÃO DE IMAGEM 🎨

| Opção | Custo | Uso | Cloud? |
|---|---|---|---|
| **Cloudflare FLUX.1-schnell** | **Grátis** ⭐ | Thumbnails, background | ✅ Sim |
| OpenRouter (vários) | $0.001-0.01/img | Qualidade máxima | ✅ Sim |

---

## 5. ARMAZENAMENTO 💾

| Serviço | Uso | Custo |
|---|---|---|
| **Cloudflare R2** | Assets, áudios, vídeos | **Grátis** (10GB) |
| **Teable** (Postgres) | Dados estruturados, tasks | Na VPS |
| **AgentMemory** | Memórias dos agentes | Na VPS |

---

## 6. RENDERIZAÇÃO DE VÍDEO 🎬

| Opção | Status | Custo |
|---|---|---|
| **Remotion + RunPod** | 🟡 Pendente configurar | $0.20/hora GPU |
| Remotion local | ❌ Queremos eliminar | — |

---

## 7. ORQUESTRAÇÃO ⚡

| Ferramenta | Status | Uso |
|---|---|---|
| **Trigger.dev** (cloud) | ✅ Deployado | Pipeline principal |
| **Hermes Agent** | ✅ Rodando | Agente Diretor |
| **Docker Compose** | ✅ Na VPS | Infra containers |

---

## 8. MAPA DE TRANSIÇÃO (Local → Cloud)

| Funcionalidade | Antes (Local) | Agora (Cloud) |
|---|---|---|
| Orquestração | Prefect | **Trigger.dev** |
| Banco | Baserow | **Teable** |
| LLM | Chave única | **OpenRouter** (multi-provedor) |
| TTS | Kokoro local | **OpenAI TTS / Edge-TTS** |
| Transcrição | Whisper local | **Groq Whisper** |
| Imagens | DALL-E local | **Cloudflare FLUX** |
| Render | Remotion local | **RunPod** (pendente) |
| Agente | Script avulso | **Hermes** (24/7) |