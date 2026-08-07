# Anatomia de uma skill

## Estrutura de pasta

```
<nome-da-skill>/           # kebab-case, orientado à tarefa (legenda-rede-social, não helper-de-legendas)
├── SKILL.md               # ≤150 linhas: frontmatter, workflow, regras duras
├── TESTES.md              # casos de teste (modo fábrica: fica só no dev; standalone: instala junto)
├── references/
│   ├── exemplos.md        # pares certo/errado comentados
│   ├── <destilado>.md     # destilado de livro, se houver (cópia — skill instalada é autocontida)
│   └── <template>.md      # templates de output, se houver
├── scripts/               # só se houver código determinístico
└── assets/                # só se houver arquivos usados no output
```

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
- A description é lida pelo Claude para DECIDIR se carrega a skill. Ela compete com dezenas de outras. Frases literais do usuário > descrições abstratas.
- Terceira pessoa ("Cria...", "Formata...", "Gera..."), nunca "Eu ajudo a...".
- Se a skill entrega arquivo, diga o formato na description ("Entrega X em Markdown e HTML").
- O bloco [QUANDO NÃO] é obrigatório quando existe skill vizinha que compartilha palavras-chave — é a única defesa contra disparo errado silencioso.

## Corpo do SKILL.md (≤150 linhas)

Ordem das seções:

1. **Propósito** — 2-3 linhas. O job e o formato do entregável.
2. **Regras duras** — o que NUNCA e o que SEMPRE. Vem antes do workflow: se só uma parte for lida, que seja essa. Cada regra com o porquê em meia linha (anti-instrução com porquê corrige mais comportamento que dez instruções positivas).
3. **Workflow** — passos numerados. Cada passo com output verificável. Passos que exigem material pesado apontam para `references/`: "Leia `references/exemplos.md` antes de escrever."
4. **Graus de liberdade** — "Fixo: A, B, C. Livre: D, E." Skill boa diz onde o modelo pode criar e onde não pode.
5. **Ponteiros** — lista dos arquivos de `references/` e quando ler cada um.

Escrita: imperativo ("Faça X", "Nunca Y"). Zero prosa motivacional, zero "você pode considerar".

O que NÃO vai no corpo:
- Exemplos longos (→ `references/exemplos.md`; exceção: 1 micro-exemplo inline se o formato de output for crítico)
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

- 3-5 pares, um por modo de falha (blocos 3 e 4 da entrevista). Pare quando o próximo par não ensina nada novo.
- Exemplos reais do usuário > exemplos sintéticos. Se sintético, valide com ele.
- Skills de voz/estilo: adicione seção "Referências de voz" com 5-8 outputs bons reais, sem par errado (aqui o volume de "certo" importa mais que o contraste).

## scripts/ e assets/

- `scripts/`: qualquer coisa determinística (conversão, validação, chamada de API) vira script chamado pelo workflow — não instrução em prosa. Prosa para julgamento, código para mecânica. Se nos testes os subagentes escreverem o mesmo helper repetidamente, isso é sinal de que ele deve virar script da skill.
- `assets/`: fontes, templates HTML, imagens que entram no output final.

## Checklist pré-instalação

- [ ] Description tem frases literais de gatilho do usuário?
- [ ] Tem [QUANDO NÃO] se existe skill vizinha?
- [ ] SKILL.md ≤150 linhas (≤500 se justificado)?
- [ ] Toda regra dura tem porquê?
- [ ] Exemplos cobrem os erros inaceitáveis do bloco 4 da entrevista?
- [ ] Os 3 testes de `testes.md` passaram (cego, baseline, gatilho)?
- [ ] Nenhum conteúdo pesado no SKILL.md que poderia estar em references/?
