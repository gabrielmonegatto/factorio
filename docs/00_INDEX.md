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
  ├── 📄 06–15                    → Docs de frente (canais, shorts, catálogo Mananciall, mineração...)
  ├── 📄 16_BLUEPRINT_AREAS.md    → ⭐ Blueprint das 7 áreas da fábrica (piloto Mananciall) + prompts das frentes
  ├── 📄 17_UNIFICACAO_DE_DADOS.md → Aposentadoria do Teable/trigger.dev + migração pro D1 (19/08)
  ├── 📄 18_AUTOMACOES.md         → ⭐ Catálogo vivo de automações (vivas/manuais/aposentadas) + doutrina do motor
  ├── 📄 22_ANCORAS_VISUAIS.md   → Âncoras dos shorts: catálogo de cenas, bíblia visual, as 10 minas do RunPod
  ├── 📄 23_PLATAFORMA_AUDIOVISUAL.md → ⭐ Tese: Magnific (ex-Freepik) como plataforma única de imagem/vídeo/música (aposenta RunPod)
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
| Notion — hub 🏭 Fábrica (gestão humana) | via kit `tools/notion/` |
| BI Mananciall (dados e curadoria) | https://bi.mananciall.org |
| BI Br4nds | https://bi.br4nds.com.br |
| VPS factorio-render | `ssh -i ~/.ssh/id_ed25519_factorio root@167.233.236.209` |

> Teable, Outline, trigger.dev e MinIO estão APOSENTADOS (docs 05 e 17). Nada vivo aponta pra eles.

## 🧠 Onde vive cada coisa (resumo — detalhe no 03 e na constituição)

| Conteúdo | Casa |
|---|---|
| Gestão humana (tarefas MACRO, roadmap, documentos) | **Notion** (cockpit do Gabriel) |
| Curadoria de catálogo e dados (Biblioteca, intel, indicadores) | **D1 + bi.mananciall.org** |
| Estado de esteira, intel, produto | **D1** |
| Código da fábrica (skills, scripts, templates, esteiras, estes docs) | **Git** (`_factorio/` e `apps/`) |
| Assets binários e arquivo morto | **R2** |
| Credenciais | `_factorio/.env` (NUNCA commitar) |

## ⚠️ Regras de ouro (herdadas e vivas)

1. *"Não minta, não tenha vergonha de falar a real, Deus abençoe."* — transparência total sobre bugs, limitações e erros.
2. **NUNCA rode `git stash pop`** no repositório EternalL (stash contém deleções massivas).
3. Pragmatismo: menos teoria, mais código executável e verificação prática.
4. O dado É o estado. 1 task = 1 operação de alto nível. (Filosofia completa no `02_OPERATING_MODEL.md`.)
