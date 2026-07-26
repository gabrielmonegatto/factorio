# ✅ CHECKLIST — Canal Spurgeon no automático

> O que falta pro ciclo virar automação no trigger.dev.
> Regra da fábrica: **não automatiza antes de sair limpo 3 vezes na mão.**
> Atualizado: 22/07/2026

---

## Onde estamos

O **pipeline de produção está pronto e validado**. Falta fechar a ponta da publicação
e provar estabilidade antes de ligar o maestro.

```
✅ narrar → ✅ legendar → ✅ renderizar (híbrido) → ✅ thumbnail → ⬜ publicar
```

---

## BLOCO A — Fechar o ciclo

| # | O quê | Quem | Status |
|---|---|---|---|
| A1 | Credencial OAuth do canal (Console + `auth_youtube.py`) | **Gabriel** (~5 min) | ⬜ |
| A2 | Gerar copy dos 93 sermões sem marketing (`generate_marketing.py`) | Claude | ⬜ |
| A3 | Narrar hook/outro dos 93 (Kokoro na VPS) | Claude | ⬜ |
| A4 | Transcrever hook/outro (AssemblyAI) → `.json` das legendas | Claude | ⬜ |
| A5 | **Publicar 1 vídeo de verdade** (agendado) — o ciclo inteiro | Claude + gate humano | ⬜ |
| A6 | **3 vídeos limpos seguidos** = critério de estável | Claude | ⬜ |

> A2→A4 é a "etapa de marketing" que estava parada — é ela que transforma
> os 93 sermões crus em renderizáveis.

---

## BLOCO B — Otimização (vale a pena antes de escalar)

| # | O quê | Ganho |
|---|---|---|
| B1 | Cortar o re-encode do concat (encodar 1x só) | **−16 min/vídeo (~27%)** |
| B2 | Bundlar o Remotion 1x em vez de 3x | −3 a 9 min/vídeo |

Medição real na KVM2 (sermão 0021): **59 min** para vídeo de 35 min.
Com B1+B2 deve cair pra ~35-40 min.

---

## BLOCO C — Virar automação

| # | O quê | Detalhe |
|---|---|---|
| C1 | **Fila no Teable** | Tabela com: sermão, status (cru→copy→narrado→renderizado→publicado), data agendada |
| C2 | **Gatilho na VPS** | Cron simples OU endpoint que o trigger.dev chama |
| C3 | **Task no trigger.dev** | Só agenda, tenta de novo se falhar e mostra o painel (**orquestrador magro**) |
| C4 | **Skill `/novo-video`** | O SOP congelado, com checklist de pronto |
| C5 | Skill `/novo-canal` | Replicar o template inteiro pra outro canal (o objetivo final) |

---

## 🔗 QR Code + i18n (decisão 24/07)

O QR de cada vídeo aponta pro NOSSO endpoint (desacoplado — destino editável sem re-render):

```
EN (padrão):   mananciall.org/go?s=yt&v=NNNN            (SEM lang)
ES/PT/outras:  mananciall.org/go?s=yt&v=NNNN&lang=es    (COM lang)
```

- `v=` = qual vídeo trouxe o scan · `s=` = origem (yt) · `lang=` = idioma (ausente = inglês)
- O `/go` (Edge Function Vercel — domínio está na Vercel, NÃO Cloudflare) loga o scan e
  redireciona: sem lang → `/en/...` · `lang=es` → `/es/...` etc.
- Implementação: 1 campo `lang` no `build_job.py` (default vazio = EN) + roteamento no backend.
- ⚠️ Domínio `mananciall.org` está na **Vercel**. Hoje `/go` cai num placeholder `/baixar` —
  o redirect+página de destino são a frente "Funil" (próximo chat: stack Cloudflare/Vercel + Stripe).

## Gates humanos (permanentes)

- 🔒 **Publicação externa** — todo upload passa por `--confirm`. A fábrica prepara, o humano libera.
- 🔒 **Credenciais** — o `refresh_token` vive no `.env` do Gabriel, nunca no código.

---

## Ordem de execução

```
A1 (Gabriel) ─┐
A2→A3→A4 ─────┼→ A5 → A6 → B1/B2 → C1→C2→C3 → C4 (skill) → C5 (replicar)
              ┘
```

A2-A4 rodam em paralelo com o A1 — não dependem da credencial.
