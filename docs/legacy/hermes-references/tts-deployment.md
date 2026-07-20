# TTS Deployment — Kokoro on VPS CPU

## Context

Kokoro is an 82M-parameter open-source TTS model used for sermon/audio narration.
It ran locally before; now it runs on the VPS CPU to eliminate local dependency.

## Why Kokoro (not cloud TTS)

| Factor | Detail |
|--------|--------|
| **Voice consistency** | Changing TTS mid-pipeline breaks voice consistency across published content |
| **Cost** | Kokoro runs free on VPS CPU (~5-10s per audio minute). Cloud alternatives cost |
| **Quality** | Kokoro handles EN, ES, PT well |
| **Cloud alternatives** | OpenAI TTS ($0.60/1M tokens), Edge-TTS (free, API), ElevenLabs (paid) |

## Deployment Options

| Option | Cost | Notes |
|--------|------|-------|
| **VPS CPU** (current) | Free | ~5-10s per audio minute. Acceptable for batch processing |
| **RunPod CPU** | ~$0.05/h | If VPS becomes overloaded |
| **RunPod GPU (T4)** | ~$0.20/h | Instantaneous, but overkill for Kokoro |
| **HuggingFace Inference (CPU)** | ~$0.06/h | More expensive than VPS, less control |

## Current Setup

- Kokoro runs as a Python process inside `factorio_agents` container
- Called by the `narrate-audio` Trigger.dev task via `pythonHelper.ts`
- Audio output goes to Cloudflare R2
- No GPU needed — 82M params fits in CPU RAM

## Future

If the VPS CPU becomes a bottleneck, the cheapest cloud upgrade is RunPod CPU
at $0.05/h. No GPU needed for Kokoro.