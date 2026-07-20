---
name: nova-skill
description: Cria ou atualiza uma skill no padrão da fábrica (SOP executável com DoD e nível de confiança). Use quando um processo repetível for identificado ou quando uma skill existente precisar absorver um aprendizado.
---

# /nova-skill — a fábrica de SOPs

**Gatilho:** processo repetível identificado, ou aprendizado que precisa virar SOP.
**Inputs:** nome + objetivo do processo (pergunte se faltar).

## Passo a passo

1. **Anti-duplicata:** liste `.claude/skills/`. Se já existe skill cobrindo o processo, proponha ATUALIZAR em vez de criar.
2. **Classifique o cérebro certo** (`docs/02_OPERATING_MODEL.md` §1):
   - Decisão em aberto → skill de sessão (siga adiante).
   - Repetitivo com prompt fixo → é LLM-função em esteira, NÃO skill — registre em `docs/backlog_skills_seed.md` e pare.
   - Sem ambiguidade nenhuma → é script puro em `scripts/` — escreva o script e pare.
3. Escreva `.claude/skills/<slug>/SKILL.md` com frontmatter (`name`, `description` com gatilho claro) e as **4 partes obrigatórias**:
   - **(a) Gatilho e inputs** — quando usar, o que ter em mãos
   - **(b) Passo a passo** — imperativo, verificável, com comandos/paths REAIS
   - **(c) Checklist de pronto (DoD)** — verificação REAL (comando que prova, nunca "parece ok")
   - **(d) Nível de confiança** — nasce `🟡 Draft — execuções limpas: 0/3`
4. **Rode 1x** (ou simule a seco se houver efeito externo/dinheiro) e ajuste o que emperrar.
5. Atualize o catálogo: linha na tabela de `.claude/skills/README.md`.
6. Commit: `skill: add /<slug>` (ou `skill: update /<slug>`).

## Regras

- Promoção 🟡→🟠→🟢 exige 3 execuções limpas consecutivas — registre a contagem no rodapé da skill.
- Gates permanentes (dinheiro · campanha · publicação externa · deleção · credenciais) NUNCA são automatizados por skill nenhuma.

## Checklist de pronto (DoD)

- [ ] SKILL.md com frontmatter + 4 partes.
- [ ] 1 execução ou simulação feita e ajustes aplicados.
- [ ] Catálogo (`README.md`) atualizado.
- [ ] Commit feito.

**Nível de confiança:** 🟡 Draft — execuções limpas: 0/3
