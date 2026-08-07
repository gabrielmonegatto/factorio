# Anatomia de uma skill

## Frontmatter (a parte mais importante da skill inteira)

```yaml
---
name: nome-da-skill
description: >
  [O QUE] Verbo + entregável + diferencial em 1-2 frases.
  [QUANDO] TRIGGER quando o usuário pedir "frase literal 1", "frase literal 2",
  "frase literal 3", ou quiser <situação descrita>.
  [QUANDO NÃO] NÃO usar para <caso vizinho> — para isso use <outra-skill>.
---
```

Regras:
- A description é lida pelo Claude para DECIDIR se carrega a skill. Ela compete com dezenas de outras. Frases literais do Pedro > descrições abstratas.
- Terceira pessoa ("Cria...", "Formata...", "Gera..."), nunca "Eu ajudo a...".
- Se a skill entrega arquivo, diga o formato na description ("Entrega X em Markdown e HTML").
- Modelo de referência do padrão da casa: descriptions de `formato-teleprompter` e `social-media-content-planner` em `~/.claude/skills/`.

## Corpo do SKILL.md (≤150 linhas)

Ordem das seções:

1. **Propósito** — 2-3 linhas. O job e o formato do entregável.
2. **Regras duras** — o que NUNCA e o que SEMPRE. Vem antes do workflow: se só uma parte for lida, que seja essa. Cada regra com o porquê em meia linha.
3. **Workflow** — passos numerados. Cada passo com output verificável. Passos que exigem material pesado apontam para `references/`: "Leia `references/exemplos.md` antes de escrever."
4. **Graus de liberdade** — "Fixo: A, B, C. Livre: D, E."
5. **Ponteiros** — lista dos arquivos de `references/` e quando ler cada um.

O que NÃO vai no corpo:
- Exemplos longos (→ `references/exemplos.md`)
- Teoria/fundamentação (→ destilado em `references/`)
- Templates de output (→ `references/template.md`)
- Explicações sobre o que são skills, como o Claude funciona, etc. (o leitor é o Claude — ele sabe)

## references/exemplos.md — formato dos pares

```markdown
## Erro 1: <nome do modo de falha>

❌ **Errado:**
<exemplo curto e real>

✅ **Certo:**
<mesmo caso, corrigido>

**Por quê:** <1-2 linhas — a regra geral que o par demonstra>
```

- 3-5 pares, um por modo de falha (blocos 3 e 4 da entrevista).
- Exemplos reais do Pedro > exemplos sintéticos. Se sintético, valide com ele.
- Skills de voz/estilo: adicione seção "Referências de voz" com 5-8 outputs bons reais, sem par errado.

## scripts/ e assets/

- `scripts/`: qualquer coisa determinística (conversão, validação, chamada de API) vira script chamado pelo workflow — não instrução em prosa. Prosa para julgamento, código para mecânica.
- `assets/`: fontes, templates HTML, imagens que entram no output final.

## Checklist pré-instalação

- [ ] Description tem frases literais de gatilho do Pedro?
- [ ] SKILL.md ≤150 linhas (≤500 se justificado)?
- [ ] Toda regra dura tem porquê?
- [ ] Exemplos cobrem os erros inaceitáveis do bloco 4 da entrevista?
- [ ] 3 casos de TESTES.md passaram?
- [ ] Gatilho testado (dispara nas frases certas, não dispara nas vizinhas)?
- [ ] Nenhum conteúdo pesado no SKILL.md que poderia estar em references/?
