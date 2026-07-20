# ⚡ WORKFLOWS — TEMPLATES TRIGGER.DEV
> Blueprint de pipelines reutilizáveis para produção em nuvem
> Baseado nos workflows Prefect antigos (scratch/workflows/)

---

## 📐 Template 1: Pipeline YouTube
**Origem:** `youtube_hunter/` + `spurgeon_generator/`

```
[discover-channels] → [classify-content] → [mine-content] → [clean-content]
                                                              ↓
                                              [narrate-audio] → [render-video]
                                                                    ↓
                                                           [publish-to-youtube]
```

| Task | ID | Provider |
|---|---|---|
| Descobrir canais | `discover-channels` | YouTube API |
| Classificar | `classify-content` | Groq/OpenRouter |
| Minerar | `mine-content` | CCEL/Python |
| Limpar | `cleanContent` ✅ | OpenRouter |
| Narrar | `narrate-audio` | Kokoro (VPS) 🟡 |
| Renderizar | `render-video` | RunPod 🟡 |
| Publicar | `publish-to-youtube` | YouTube API |

**Cron:** A cada 6h | **Status:** 🟡 Falta RunPod

---

## 📐 Template 2: Publisher de Livros ✅
**Origem:** `mananciapp/` (já deployado)

```
[translate-content] → [publish-book]
```

| Task | ID | Provider | Status |
|---|---|---|---|
| Traduzir | `translate-content` | OpenRouter | ✅ Deployado |
| Publicar | `publishBook` | Astro/Markdown | ✅ Deployado |
| Limpar | `cleanContent` | OpenRouter | ✅ Deployado |

**Cron:** Diário (22h) | **Status:** ✅ Pronto

---

## 📐 Template 3: Clips Factory
**Origem:** `motoropus_clipper/`

```
[channel-watchdog] → [discover-clips] → [process-clip] → [batch-render]
```

| Task | Provider |
|---|---|
| Watchdog | Trigger.dev schedule |
| Descobrir | YouTube API |
| Processar | FFmpeg worker |
| Renderizar | RunPod 🟡 |

**Status:** 🟡 Precisa RunPod

---

## 📐 Template 4: Asset Generator ✅
**Origem:** `marketing_assets_generator.py` + `image_engine_cf.py`

```
[generate-thumbnail] → [generate-marketing] → [fetch-audio-assets]
```

| Task | Provider | Status |
|---|---|---|
| Thumbnail | Cloudflare FLUX | 🟡 Não deployado |
| Marketing copy | OpenRouter | ✅ Deployado (`marketing.ts`) |
| Assets áudio | Freesound API | 🟡 Não deployado |

**Status:** Parcialmente deployado

---

## 📐 Template 5: Content Mining
**Origem:** `site_miner/` + `workflow_mineracao/`

```
[discover-source] → [scrape-content] → [catalog-content] → [enrich-content]
```

**Status:** ⬜ Próximo a converter

---

## 🎯 Prioridade para Implementação

| # | Template | Impacto | Já temos? |
|---|---|---|---|
| 1 | **Publisher Livros** | 🔥🔥🔥🔥🔥 | ✅ 100% |
| 2 | **Asset Generator** | 🔥🔥🔥🔥 | ✅ 50% |
| 3 | **YouTube Pipeline** | 🔥🔥🔥🔥🔥 | 🟡 Falta RunPod |
| 4 | **Content Mining** | 🔥🔥🔥 | ⬜ |
| 5 | **Clip Factory** | 🔥🔥 | ⬜ |