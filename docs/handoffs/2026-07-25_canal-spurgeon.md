# Handoff — Canal Spurgeon (fábrica de vídeo) — 25/07/2026

> Frente: fábrica de vídeo do canal **Charles Spurgeon Treasures** (1º template da fábrica).
> Sessão nova: leia isto + `docs/07_ROADMAP_CANAL_SPURGEON.md` + memória `factory-redesign`.

## Estado atual (o que ESTÁ feito + como verificar)

**A fábrica de vídeo está NO AR e AUTÔNOMA na Hetzner.**

- **Infra:** VPS Hetzner CX53 (16 vCPU/32GB/x86, Falkenstein), IP `167.233.236.209`, SSH `~/.ssh/id_ed25519_factorio` (user root). Hostinger antiga (`187.127.44.153`) ainda LIGADA mas já sem uso — Gabriel vai derrubar.
  - Verificar: `ssh -i ~/.ssh/id_ed25519_factorio root@167.233.236.209 "docker ps"`
- **Render híbrido validado:** ~18min/vídeo na CX53 (era ~59min na KVM2). Remotion (clipes curtos) + ffmpeg (corpo estático + legenda .ass idêntica ao Remotion, fonte Georgia). Pipeline: `hybrid_render.py` (via `docker/factory.sh render N`).
- **Teable migrado** pra Hetzner: `https://db.markeologia.com.br` (HTTP 307 ok, cert Caddy emitido, DNS nuvem CINZA na CF conta gabriel.monegatto). Dados validados íntegros (só drift de 37 thumbnails + migrations novas). Backup no R2 `backups/teable/teable_2026-07-25_hetzner.dump`.
  - Verificar: `curl -sI https://db.markeologia.com.br` → 307.
- **YouTube:** canal Charles Spurgeon Treasures conectado (creds `.env` → `YT_CLIENT_ID/SECRET/REFRESH_TOKEN`). 3 vídeos AGENDADOS (privados→públicos): 0001→27/jul, 0002→28, 0003→29, 12:00 UTC.
- **Produção 24/7 (fábrica viva)** — serviço systemd `factory-producer.service` na VPS (28/07):
  - Roda `render_buffer.py --loop --cpus 8`: renderiza um sermão após o outro, sem parar, até a fila esvaziar; fila vazia → dorme 30min e recheca. `Restart=always` + `WantedBy=multi-user` → sobrevive a crash e reboot.
  - Usa 8 dos 16 núcleos (deixa 8 pro Teable). Load típico em produção ~8-9.
  - Verificar: `ssh ... "systemctl status factory-producer; tail -20 /var/log/factory_producer.log; docker ps"`.
  - **O cron antigo `render_buffer --count 2` (a cada 4h) foi DESLIGADO** (comentado em `/etc/cron.d/factory`) — o serviço assumiu a produção. Não religar os dois juntos (render duplo = 16 núcleos, sufoca o Teable).
- **Agendamento (publicação)** — cron `schedule_channel.py` (diário 06:00 UTC) em `/etc/cron.d/factory`: agenda vídeos renderizados no calendário via `publishAt`. Calendário: 1/dia por 14 dias → 2/dia (12:00 e 23:00 UTC). Ordem sequencial. Estado em R2 `schedule/spurgeon_schedule.json`.
  - Verificar: `ssh ... "cat /etc/cron.d/factory; tail /var/log/factory_schedule.log"`
- **Acervo:** ~113 sermões, 112 narrados (Kokoro), copy visceral gerado nos 113 (`generate_marketing.py`: título "(Charles Spurgeon)" + thumbnailText ≤6 palavras + videoDescription SEM revelar fonte). Buffer inicial de 14 vídeos renderizando quando este handoff foi escrito.

## Próximos passos (em ordem)

1. **Housekeeping do Gabriel (não-técnico, sem pressa):** derrubar a Hostinger; revogar tokens expostos no chat (`HETZNER_API_TOKEN`, PAT Docker Hub).
2. **Confirmar a automação girando** (após 26-27/jul): `tail /var/log/factory_*.log` na VPS — ver render_buffer renderizando e schedule_channel agendando os próximos. Conferir no YouTube Studio que 0004+ aparecem agendados.
3. **Funil** (frente nova): `mananciall.org/go` hoje cai em placeholder `/baixar`. Domínio está na **Vercel** (não CF). Construir: Edge Function redirect (`?s=yt&v=NNNN&lang=xx`; EN=sem lang → loga scan + UTMs) + página EN de livros do Spurgeon + Stripe. QR já aponta pra esse endpoint (desacoplado).
4. **Fábrica de shorts:** cortes verticais do sermão → Insta/TikTok (lane separada; reaproveita o render + passo de clipagem).
5. **Refino:** congelar `/novo-video` como skill; migrar estado do agendador (JSON no R2) pro Teable.

## Minas e gotchas (o que pode explodir / NÃO fazer)

- **`python`/`uv` local tem cert SSL EXPIRADO** → pra APIs use `curl` ou o Python310 (`C:/Users/Monegatto/AppData/Local/Programs/Python/Python310/python.exe`). Na VPS, `python3` normal funciona.
- **`/tmp` do Git bash ≠ path do Python310 (Windows)** — ao passar arquivos entre eles, use o scratchpad ou `docker cp`.
- **DNS na Cloudflare TEM que ser nuvem CINZA (DNS-only)** pro Caddy emitir SSL. Laranja (proxy) → erro 525.
- **Áudio dos sermões: 44 em `.wav`, 68 em `.mp3`** — `build_job.py` já trata os dois; não assumir só wav.
- **Comentário no YouTube precisa scope `youtube.force-ssl`** (auth atual só `upload`) → link fica na DESCRIÇÃO, não em comentário fixado (API não fixa comentário de qualquer forma). `auth_youtube.py` já tem o scope novo pra próxima re-auth.
- **NUNCA revelar a fonte** (sermão original/domínio público) na descrição — regra do Gabriel, já no prompt do `generate_marketing.py`.
- Imagens Docker: uma sessão paralela já apagou as imagens da VPS uma vez (`docker prune`). Rebuild leva ~15min. (Considerar push pro Docker Hub como backup.)
- Render de vídeo longo full-Remotion = bug do vídeo de 3h (duração hardcoded). JÁ resolvido via `calculateMetadata` — não reintroduzir.

## Credenciais/paths (referência, nunca o valor)

- `_factorio/.env` (local) e `/srv/factorio/.env` (VPS): `R2_*`, `YT_CLIENT_ID/SECRET/REFRESH_TOKEN`, `OPENROUTER_API_KEY`, `ASSEMBLYAI_API_KEY`, `HETZNER_API_TOKEN` (revogar), `CLOUDFLARE_API_TOKEN` (conta Br4nds — NÃO alcança markeologia.com.br, que está na conta gabriel.monegatto).
- Scripts da fábrica em `_factorio/remotion/`: `build_job.py`, `subtitle_ass.py`, `hybrid_render.py`, `generate_marketing.py`, `narrate_marketing.py`, `publish_sermon.py`, `publish_youtube.py`, `schedule_channel.py`, `render_buffer.py`. Compose do Teable + factory.sh + Dockerfile.tts em `_factorio/docker/`.
- R2 bucket `mananciall`: sermões em `channels/channels_youtube/treasures_charlesspurgeon/NNNN_-_*/`, vídeos em `renders/spurgeon/NNNN.mp4`, estado do agendador em `schedule/spurgeon_schedule.json`, backups em `backups/teable/`.
- YouTube videoIds: 0001=`t12Ml4-C5m0`, 0002=`A21zMhdAvoM`, 0003=`Rgh2fyiEYmI`.
