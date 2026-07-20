# 🏗️ TEMPLATES TRIGGER.DEV — FÁBRICA ETERNALL
> Blueprint de workflows reutilizáveis para produção em nuvem
> Baseado nos workflows Prefect antigos (scratch/workflows/)
> Atualizado: 08/07/2026

---

## 📐 Template 1: YouTube Channel Pipeline
**Baseado em:** `youtube_hunter/` + `spurgeon_generator/`

```
[discover-channels] → [classify-content] → [mine-content] → [clean-content]
                                                              ↓
                                              [narrate-audio] → [render-video]
                                                                    ↓
                                                           [publish-to-youtube]
```

| Task | Trigger ID | Provider | Custo |
|---|---|---|---|
| Descobrir canais | `discover-channels` | YouTube API | Grátis |
| Classificar conteúdo | `classify-content` | Groq/OpenRouter | Grátis |
| Minerar conteúdo | `mine-content` | CCEL/OpenRouter | ~$0.05 |
| Limpar conteúdo | `cleanContent` | OpenRouter | ~$0.02 |
| Narrar áudio | `narrate-audio` | OpenAI TTS | ~$0.01/min |
| Renderizar vídeo | `render-video` | RunPod 🟡 | ~$0.20/h |
| Publicar YouTube | `publish-to-youtube` | YouTube API | Grátis |

**Starter cron:** A cada 6h
**Payload:** `{ brand: "mananciall", projectSlug: "yt_en_treasures_spurgeon" }`

---

## 📐 Template 2: Book Publishing Pipeline
**Baseado em:** `spurgeon_generator/publishBook` + `cleaner`

```
[translate-content] → [review-translation] → [publish-book]
```

| Task | Trigger ID | Provider |
|---|---|---|
| Traduzir conteúdo | `translate-content` | OpenRouter |
| Publicar livro | `publishBook` | Astro/Markdown |

**Starter cron:** Diário (22h)
**Payload:** `{ projectIndexId: "...", limit: 10 }`

---

## 📐 Template 3: Clip Factory
**Baseado em:** `motoropus_clipper/`

```
[channel-watchdog] → [discover-clips] → [process-clip] → [batch-render]
```

| Task | Trigger ID | Provider |
|---|---|---|
| Watchdog de canais | `channel-watchdog` | Trigger.dev schedule |
| Descobrir clipes | `discover-clips` | YouTube API |
| Processar clipe | `process-clip` | FFmpeg (worker) |
| Renderizar lote | `batch-render` | RunPod 🟡 |

---

## 📐 Template 4: Asset Generator
**Baseado em:** `marketing_assets_generator.py` + `image_engine_cf.py`

```
[generate-thumbnail] → [generate-marketing] → [generate-audio-assets]
```

| Task | Trigger ID | Provider |
|---|---|---|
| Gerar thumbnail | `generate-thumbnail` | Cloudflare FLUX |
| Gerar copy marketing | `marketing` | OpenRouter |
| Buscar assets áudio | `fetch-audio-assets` | Freesound API |

---

## 📐 Template 5: Content Mining Pipeline
**Baseado em:** `site_miner/` + `workflow_mineracao/`

```
[discover-source] → [scrape-content] → [catalog-content] → [enrich-content]
```

| Task | Trigger ID | Provider |
|---|---|---|
| Descobrir fonte | `discover-source` | OpenRouter |
| Extrair conteúdo | `scrape-content` | Python worker |
| Catalogar | `catalog-content` | Teable DB |
| Enriquecer | `enrich-content` | OpenRouter |

---

## 🎯 PRIORIDADE DOS TEMPLATES

| # | Template | Complexidade | Impacto | Dependência |
|---|---|---|---|---|
| 1 | **YT Pipeline** | Média | 🔥🔥🔥🔥🔥 | RunPod 🟡 |
| 2 | **Book Publishing** | Baixa | 🔥🔥🔥🔥 | Nenhuma ✅ |
| 3 | **Content Mining** | Média | 🔥🔥🔥 | Nenhuma ✅ |
| 4 | **Asset Generator** | Baixa | 🔥🔥🔥 | Nenhuma ✅ |
| 5 | **Clip Factory** | Alta | 🔥🔥 | RunPod 🟡 |

---

## 🔧 PRÓXIMOS PASSOS

1. ✅ **Book Publishing** — já temos `publishBook.ts` e `cleanContent.ts` deployados
2. ✅ **Asset Generator** — já temos `marketing.ts` deployado  
3. 🟡 **YT Pipeline** — precisa do RunPod pra render + decidir TTS cloud
4. ⬜ **Content Mining** — converter `site_miner/` pra Trigger.dev
5. ⬜ **Clip Factory** — depois dos outros