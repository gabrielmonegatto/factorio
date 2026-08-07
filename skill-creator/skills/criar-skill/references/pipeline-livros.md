# Pipeline de livros → destilado

Livro nunca entra cru numa skill. Um livro de 300 páginas vira um destilado de 200-400 linhas que o Claude consegue carregar sob demanda. **Preferir sempre o livro integral ao resumo** (Bookey etc.): diálogos canônicos e números de pesquisa só existem no integral.

## Onde o destilado mora

- **Modo fábrica**: em `destilados/<autor>-<titulo-curto>.md` — REUTILIZÁVEL entre skills. Antes de destilar, verifique se já existe; se sim, use-o (no máximo complemente). Na instalação, copie para a `references/` da skill (skills instaladas são autocontidas).
- **Modo standalone**: direto em `references/<autor>-<titulo-curto>.md` da skill. Avise o usuário que o destilado não ficará arquivado para reúso — se ele quiser, pode copiá-lo para a fábrica depois.

## Passo a passo

1. **Receber**: o usuário indica o arquivo (PDF, EPUB ou MD). Se EPUB, converta para texto antes de ler.
2. **Verificar duplicata** (modo fábrica): já existe destilado desse livro em `destilados/`?
3. **Mapear**: leia o sumário e identifique os capítulos relevantes PARA A SKILL em questão. Não destile o livro inteiro por padrão — destile o que serve ao job. (Se o usuário disser "esse livro inteiro é a base", aí sim destilado completo.)
4. **Extrair** (o que entra no destilado):
   - **Frameworks e modelos** — os sistemas nomeados do autor, com os passos
   - **Regras operacionais** — tudo que é "faça X / nunca Y" acionável
   - **Vocabulário** — os termos que o autor cunhou, com definição de 1 linha
   - **Exemplos canônicos** — os 2-3 melhores casos que o autor usa
   - **Contra-intuitivos** — onde o autor contradiz o senso comum (é o que diferencia o destilado de conhecimento genérico que o Claude já tem)
5. **Descartar** (o que NÃO entra): histórias motivacionais, biografia do autor, repetições, capítulos de venda do próximo livro, tudo que o Claude já sabe por conhecimento geral.
6. **Formatar** com cabeçalho:

```markdown
# Destilado: <Título> — <Autor>
> Fonte: <livro>, destilado em <data>. Capítulos cobertos: <quais>.
> Usado pelas skills: <lista, manter atualizada>

## Frameworks
## Regras operacionais
## Vocabulário
## Exemplos canônicos
## Contra-intuitivos
```

7. **Validar com o usuário**: mostre o destilado e pergunte "o que desse livro você usa que não está aqui?". A resposta é frequentemente o insight mais valioso — quem leu e aplicou sabe o que o sumário não mostra.
8. **Conectar**: no SKILL.md da skill, aponte: "Antes de <passo>, leia `references/<destilado>.md`".

## Teste do destilado

Pergunta de controle: "Se eu ler só o destilado, executo a tarefa no nível de quem leu o livro?" Se a resposta for não, falta regra operacional — volte ao passo 4. Se o destilado passou de ~500 linhas, sobrou teoria — volte ao passo 5.
