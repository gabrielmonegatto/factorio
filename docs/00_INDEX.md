# 🏭 FÁBRICA ETERNALL — ÍNDICE DA DOCUMENTAÇÃO

> Mapa de navegação da Fábrica (Factorio). Toda sessão nova começa aqui.
> **Última reescrita: 18/07/2026** — redesenho completo em torno do Claude Max.
> Os documentos antigos (era Hermes/agentes Python) estão preservados em `legacy/`.

---

## 📂 Estrutura

```
📁 _factorio/docs/
  ├── 📄 00_INDEX.md              ← Você está aqui
  ├── 📄 01_MASTERPLAN.md         → Visão, tese, decisões e racional
  ├── 📄 02_OPERATING_MODEL.md    → COMO a fábrica funciona (o fluxo padrão de tudo)
  ├── 📄 03_DATA_ARCHITECTURE.md  → Onde vive cada dado (Outline/Teable/git/D1/R2)
  ├── 📄 04_ROADMAP.md            → Fases, critérios de pronto, decisões em aberto
  ├── 📄 05_LEGACY_TRANSITION.md  → Aposentadoria da camada antiga, peça por peça
  ├── 📄 STACK.md                 → Infra da VPS (era 1.0 — infra vale, modelo de agentes não)
  ├── 📄 backlog_skills_seed.md   → Backlog bruto de workflows/skills por área (seed do catálogo)
  └── 📁 legacy/                  → Docs da era anterior (histórico, não seguir)
```

> **Desenho do terreno (20/07/2026):** `EternalL/` não é mais repo — é o terreno com dois reinos: `_factorio/` (SUBSOLO, a fábrica, este repo) e `apps/` (SUPERFÍCIE, os frutos, cada um repo próprio). Placa em `EternalL/CLAUDE.md`; constituição em `_factorio/CLAUDE.md`; skills em `_factorio/.claude/skills/`.

## 📋 Ordem de leitura

| # | Documento | O que responde | Leitura |
|---|---|---|---|
| 1 | `01_MASTERPLAN.md` | O que é a fábrica, por que este desenho | ✅ Obrigatória |
| 2 | `02_OPERATING_MODEL.md` | Como QUALQUER trabalho acontece aqui | ✅ Obrigatória |
| 3 | `03_DATA_ARCHITECTURE.md` | Onde ler/escrever cada tipo de dado | ✅ Obrigatória |
| 4 | `04_ROADMAP.md` | O que estamos construindo agora | ✅ Antes de agir |
| 5 | `05_LEGACY_TRANSITION.md` | O que está sendo aposentado e como | 🔧 Consulta |

## 🔗 Links rápidos

| Recurso | Link |
|---|---|
| Teable (dados operacionais) | https://db.markeologia.com.br |
| Outline Holding (wiki EternalL) | https://admin.markeologia.com.br |
| Outline Br4nds (wiki Br4nds) | https://admin.br4nds.com.br |
| Trigger.dev Dashboard | https://cloud.trigger.dev/projects/v3/proj_dsuhcyzyqgruytusyipj |
| MinIO Console | https://minio.markeologia.com.br |

## 🧠 Onde vive cada coisa (resumo — detalhe no 03)

| Conteúdo | Casa |
|---|---|
| Narrativa de negócio (wiki, briefings, análises, decisões) | **Outline** |
| Dados operacionais tabulares (tasks, índices, chunks, pipeline state) | **Teable** |
| Código da fábrica (skills, scripts, templates, esteiras, estes docs) | **Git** (`_factorio/` e `apps/`) |
| Dados de produto em produção (tracking, leads, vendas) | **D1** (Cloudflare) |
| Assets binários (áudio, vídeo, imagens) | **R2 / MinIO** |
| Credenciais | `_factorio/.env` (NUNCA commitar) |

## ⚠️ Regras de ouro (herdadas e vivas)

1. *"Não minta, não tenha vergonha de falar a real, Deus abençoe."* — transparência total sobre bugs, limitações e erros.
2. **NUNCA rode `git stash pop`** no repositório EternalL (stash contém deleções massivas).
3. Pragmatismo: menos teoria, mais código executável e verificação prática.
4. O dado É o estado. 1 task = 1 operação de alto nível. (Filosofia completa no `02_OPERATING_MODEL.md`.)
