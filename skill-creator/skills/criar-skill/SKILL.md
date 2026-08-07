---
name: criar-skill
description: >
  Cria, testa, instala e conserta skills de Claude Code pelo processo da fábrica:
  entrevista de 8 blocos, matéria-prima destilada (livros viram destilado, nunca entram crus),
  rascunho com divulgação progressiva, teste cego com baseline (com/sem skill) e teste de
  gatilho com near-misses, instalação em ~/.claude/skills/. TRIGGER quando o usuário pedir
  "cria uma skill", "quero uma skill que...", "transforma isso numa skill", "vira skill",
  "melhora a skill X", "conserta a skill X", "a skill X errou". NÃO usar para configurar
  o harness, hooks, permissões ou settings.json (use update-config), nem para criar
  subagentes em .claude/agents/ (anatomia diferente).
---

# Criar Skill

## Propósito

Conduz o ciclo de vida completo de uma skill: nascer (entrevista → matéria-prima → rascunho → teste → instalação), evoluir e ser consertada. O produto final é uma pasta em `~/.claude/skills/<nome>/` que passou nos três testes: qualidade cega, baseline e gatilho.

## Passo 0 — Detectar o ambiente (sempre primeiro)

Verifique se a fábrica está montada: `/Volumes/KINGSTON/claude/tools/skill-creator/` (teste também `/Volumes/Kingston/...`).

- **Modo fábrica** (pasta existe): desenvolva em `skills/<nome>/` de lá. Arquive a entrevista em `entrevistas/<nome>.md` e destilados em `destilados/` — destilados são REUTILIZÁVEIS entre skills; antes de destilar, verifique se já existe.
- **Modo standalone** (pasta não existe): desenvolva no diretório temporário da sessão. Na instalação, o `TESTES.md` vai junto para `~/.claude/skills/<nome>/` — é a única cópia de desenvolvimento que existirá.

Não pergunte ao usuário qual modo usar; a detecção decide.

## Regras duras

1. **Divulgação progressiva.** A `description` carrega em TODAS as sessões (~100 palavras); o SKILL.md carrega quando dispara (≤150 linhas, 500 no limite absoluto); o peso mora em `references/`, lido sob demanda. Se algo pode viver em `references/`, vive em `references/` — cada linha no lugar errado custa contexto para sempre.
2. **Nunca pule a entrevista.** Nem por achar que já sabe a resposta. Os blocos 3 e 4 (barra de qualidade e modos de falha) são a matéria-prima dos exemplos certo/errado — sem eles a skill nasce genérica.
3. **A description decide o disparo.** Frases literais do usuário no TRIGGER + "NÃO usar para X → use Y" quando houver skill vizinha que confunda. Description abstrata = skill que não dispara ou dispara errado.
4. **Livro nunca entra cru.** Um livro vira destilado de 200-400 linhas antes de alimentar qualquer skill (`references/pipeline-livros.md`).
5. **Skill não está pronta quando compila — está pronta quando passa nos testes.** Qualidade cega, baseline e gatilho com near-misses, antes de instalar. Sem exceção.
6. **Regra dura sem porquê não entra.** "Nunca faça X" só vale com "(porque Y)" — o modelo obedece melhor o que entende.
7. **Um par de exemplos por modo de falha.** 3-5 pares certo/errado, cada um ensinando um erro DIFERENTE. Dois pares que ensinam o mesmo erro = delete um. Nunca 10+10: redundância dilui o sinal.

## Workflow — criar skill nova

1. **Entrevista.** Conduza `references/entrevista.md` (8 blocos) como conversa. Output: síntese confirmada pelo usuário (arquive conforme o modo do Passo 0).
2. **Matéria-prima.** Livro → `references/pipeline-livros.md`. Peça exemplos reais de trabalho do usuário, bons E ruins — valem mais que exemplos inventados.
3. **Rascunho.** Siga `references/anatomia.md`. Escreva o SKILL.md primeiro, depois os references. **Mostre o rascunho ao usuário antes de testar.**
4. **Teste.** Siga `references/testes.md`: (a) 3 casos cegos em subagente contra a barra da entrevista; (b) 1 baseline sem a skill — se o output for igual, a skill não agrega: reescreva ou aborte; (c) gatilho com ~10 queries, metade should-trigger, metade near-miss. Cada falha vira correção no SKILL.md ou novo par certo/errado.
5. **Instalação.** `cp -R <rascunho> ~/.claude/skills/<nome>` (modo fábrica: TESTES.md fica só no dev; standalone: vai junto). Confirme que a skill aparece disponível em sessão nova.

## Workflow — consertar skill existente

1. Localize a cópia de desenvolvimento (fábrica `skills/<nome>/` se existir; senão a instalada em `~/.claude/skills/<nome>/` é o dev).
2. Reproduza o erro num subagente antes de mexer — conserto sem reprodução é chute.
3. Corrija e **transforme o erro em par "errado" comentado** em `references/exemplos.md` (porque o erro que aconteceu uma vez acontece de novo).
4. Re-rode o caso de teste que falhou + os casos existentes do TESTES.md. Reinstale.

## Graus de liberdade

- **Fixo:** ordem das 5 fases, os 3 testes antes de instalar, estrutura de pasta, fórmula da description, limites de linhas, um par por modo de falha.
- **Livre:** profundidade da entrevista (skill simples = blocos podem ser rápidos), formato interno dos references, quantos casos de teste além dos 3 mínimos, tom da escrita do corpo (desde que imperativo).

## Ponteiros

- `references/entrevista.md` — os 8 blocos; leia ANTES de iniciar a fase 1.
- `references/anatomia.md` — frontmatter, corpo, exemplos, checklist pré-instalação; leia antes da fase 3.
- `references/pipeline-livros.md` — livro → destilado; leia só se houver livro/curso como fonte.
- `references/testes.md` — protocolo dos 3 testes (cego, baseline, gatilho); leia antes da fase 4.
