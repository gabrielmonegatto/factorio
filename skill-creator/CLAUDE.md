# Skill Creator

> **Memória do projeto:** leia CONTEXTO.md antes de começar qualquer trabalho.
> Ao fechar uma sessão de trabalho, atualize-o (skill memoria-projeto).

Este projeto é a fábrica de Skills do Pedro. Toda skill nova para Claude Code nasce aqui: entrevista → matéria-prima → rascunho → teste → instalação em `~/.claude/skills/`.

## Regra de ouro: divulgação progressiva

O contexto é o recurso mais caro. Uma skill tem 3 camadas de carga:

1. **`description` (frontmatter)** — sempre carregada, em TODAS as sessões. É o que decide se a skill dispara. ~100 palavras, nem uma a mais do que o necessário.
2. **`SKILL.md` (corpo)** — carregado quando a skill dispara. Máximo 150 linhas na maioria dos casos, 500 no limite absoluto. Contém o workflow e as regras duras.
3. **`references/`** — carregado sob demanda, quando o SKILL.md manda ler. Aqui mora o peso: exemplos, destilados de livros, templates.

Se algo pode viver em `references/` em vez do SKILL.md, vive em `references/`.

## Fluxo de criação de uma skill (sempre nesta ordem)

### Fase 1 — Entrevista
Antes de escrever qualquer linha, conduza a entrevista de `references/entrevista-skill.md`. Não pule perguntas por achar que já sabe a resposta. O objetivo é extrair: o job, os gatilhos, a barra de qualidade, os modos de falha e as fontes de expertise.

### Fase 2 — Matéria-prima
- **Livros**: se o Pedro mandar um livro, siga `references/pipeline-livros.md`. Nunca cole o livro na skill — destile.
- **Exemplos reais**: peça exemplos de trabalho do Pedro (bons E ruins). Exemplos reais dele valem mais que exemplos que você inventa.

### Fase 3 — Rascunho
Crie a skill em `skills/<nome>/` seguindo `references/anatomia-skill.md`. Escreva o SKILL.md primeiro, depois os references. Mostre o rascunho ao Pedro antes de testar.

### Fase 4 — Teste (não pule)
Uma skill não está pronta quando compila — está pronta quando passa nos testes:
1. Escreva 3 casos de teste em `skills/<nome>/TESTES.md`: input real → output esperado.
2. Rode cada caso (em subagente ou sessão nova) e compare com a barra de qualidade da entrevista.
3. Teste o gatilho: as frases que o Pedro disse na entrevista disparam a skill? Frases parecidas mas fora de escopo NÃO disparam?
4. Cada falha vira uma correção no SKILL.md ou um novo par certo/errado nos exemplos.

### Fase 5 — Instalação e iteração
```bash
cp -R skills/<nome> ~/.claude/skills/<nome>
```
A versão canônica fica em `~/.claude/skills/`; a cópia aqui é o ambiente de desenvolvimento. Quando o Pedro reportar um erro da skill em uso, o conserto é feito aqui e reinstalado — e o erro vira exemplo "errado" na skill.

## Estrutura padrão de toda skill criada

```
<nome-da-skill>/
├── SKILL.md              # ≤150 linhas: frontmatter, workflow, regras duras
├── TESTES.md             # casos de teste (fica só no dev, não instala)
├── references/
│   ├── exemplos.md       # pares certo/errado comentados
│   ├── <destilado>.md    # destilado de livro, se houver
│   └── <template>.md     # templates de output, se houver
├── scripts/              # só se houver código determinístico
└── assets/               # só se houver arquivos usados no output
```

## Regras de escrita (inegociáveis)

- **Nome**: kebab-case, orientado à tarefa (`legenda-rede-social`, não `helper-de-legendas`).
- **Description**: em português, terceira pessoa, com duas partes: (1) o que a skill faz e entrega, (2) `TRIGGER quando o usuário...` com as frases literais que o Pedro usa. Copie o padrão de `formato-teleprompter` e `social-media-content-planner`. Inclua também quando NÃO usar, se houver skill vizinha que confunda.
- **Corpo em imperativo**: "Faça X", "Nunca Y". Zero prosa motivacional, zero "você pode considerar".
- **Graus de liberdade explícitos**: separe o que é regra dura (checklist, sempre igual) do que é critério (heurística, julgamento). Skill boa diz onde o modelo pode criar e onde não pode.
- **Workflows numerados**: procedimento = passos numerados com output verificável por passo.
- **Anti-instruções valem mais**: "Nunca faça X (porque Y)" corrige mais comportamento que dez instruções positivas.

## Exemplos: quantos e como

Qualidade e contraste valem mais que volume. A regra não é um número — é **um par por modo de falha**:

- **Pares certo/errado**: 3 a 5 pares, cada par ensinando um erro DIFERENTE, sempre com uma linha de "por quê". Dois pares que ensinam o mesmo erro = delete um.
- **Skills de voz/estilo**: 5 a 8 exemplos bons de output real do Pedro (aqui o volume de "certo" importa mais que o contraste).
- **Nunca 10+10**: exemplos redundantes incham o contexto e diluem o sinal. Pare de adicionar quando o próximo exemplo não ensina nada novo.
- Exemplos moram em `references/exemplos.md`, não no SKILL.md (exceto 1 micro-exemplo inline se o formato de output for crítico).

## Estrutura deste projeto

```
skill-creator/
├── CLAUDE.md             # este arquivo
├── references/           # manuais do processo de criação
├── entrevistas/          # transcrição da entrevista de cada skill
├── livros/               # livros crus que o Pedro mandar (PDF/EPUB/MD)
├── destilados/           # destilados de livros — REUTILIZÁVEIS entre skills
└── skills/               # rascunhos em desenvolvimento
```

Antes de destilar um livro, verifique se já existe destilado em `destilados/`. Um livro destilado uma vez serve a várias skills.
