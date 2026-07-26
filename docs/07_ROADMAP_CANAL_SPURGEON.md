# 🗺️ ROADMAP — Canal Spurgeon (fábrica de vídeo)

> Onde estamos e o que falta. Atualizado: 25/07/2026.
> Fábrica de vídeo do canal **Charles Spurgeon Treasures** — o primeiro template da fábrica.

---

## ✅ JÁ CONSTRUÍDO (a fábrica funciona ponta a ponta)

| Peça | Estado |
|---|---|
| **Pipeline de vídeo** narrar→transcrever→renderizar→thumbnail→publicar | ✅ 100% |
| **Render híbrido** (Remotion clipes + ffmpeg corpo) ~10x mais barato | ✅ |
| **Legenda idêntica** ao Remotion (Georgia, gerada em .ass) | ✅ |
| **Copy visceral** dos 113 sermões (título + thumbnail + descrição) | ✅ |
| **Narração** de 112 sermões (Kokoro) — acervo ~4 meses de canal | ✅ |
| **Publicação no YouTube** (privado/agendado + thumbnail + link) | ✅ |
| **3 vídeos publicados** (0001, 0002, 0003) privados pra revisão | ✅ |
| **Migração pra Hetzner CX53** (16 núcleos, 3,3x mais rápido) | ✅ render+tts |
| **Teable migrado** pra Hetzner (dados restaurados, rodando) | ✅ falta só DNS |

---

## ✅ MIGRAÇÃO FECHADA (25/07)

- DNS `db.markeologia.com.br` → 167.233.236.209 (Hetzner) ✅
- HTTPS ok (cert Caddy emitido, nuvem cinza) ✅
- Banco validado (dados íntegros) + backup no R2 ✅
- **Fábrica 100% na Hetzner** (render + tts + Teable)

### Falta só (Gabriel):
- **Derrubar a Hostinger** (não é mais usada)
- **Revogar tokens expostos** (Hetzner API, Docker PAT)

---

## ✅ CANAL NO AUTOMÁTICO (25/07)

**Set-and-forget rodando na Hetzner:**
- Calendário: 1/dia (2 semanas) → 2/dia · 12:00 e 23:00 UTC (~8h/19h ET) · sequencial
- **3 vídeos agendados** (0001→27/jul, 0002→28, 0003→29) — YouTube publica sozinho
- `schedule_channel.py` (cron diário 06:00) — agenda vídeos renderizados no calendário via `publishAt`
- `render_buffer.py` (cron a cada 4h) — mantém o estoque de render à frente
- Estado no R2: `schedule/spurgeon_schedule.json`
- Buffer inicial de 14 vídeos renderizando agora

**A fábrica produz e publica sozinha. Gabriel não toca em nada.**

### Falta (refino, não bloqueia):
- Congelar como skill `/novo-video` (SOP)
- Migrar o estado do agendador pro Teable (hoje é JSON no R2 — funciona)

---

## 🟢 DEPOIS (expansão)

| Frente | O quê |
|---|---|
| **Funil** | Worker/Edge `mananciall.org/go` (redirect + log) + página EN + Stripe |
| **i18n** | Traduzir vídeos (ES/PT) — QR já suporta `&lang=` |
| **Fábrica de shorts** | Cortes verticais do sermão → Insta/TikTok (lane de curtos) |
| **Canal 2** | Replicar o template inteiro → skill `/novo-canal` |

---

## 🖥️ Infra atual

| | Hostinger KVM2 (velha) | **Hetzner CX53 (nova)** |
|---|---|---|
| Núcleos/RAM | 2 / 8GB | **16 / 32GB** |
| Render por vídeo | ~59 min | **~18 min** |
| IP | 187.127.44.153 | **167.233.236.209** |
| Roda | (desligar após DNS) | render + tts + Teable |
| Custo | R$197/mês mensal | ~€35/mês (~R$224) |

**Regra:** Hetzner = cavalo de trabalho (render/narração/Teable). RunPod = reserva pra surto/GPU.

---

## ⚠️ Pendências de segurança
- Revogar: token Hetzner, PAT Docker Hub, credenciais coladas no chat
- Funil `mananciall.org` está na **Vercel** (não Cloudflare); `/go` hoje cai em placeholder `/baixar`
