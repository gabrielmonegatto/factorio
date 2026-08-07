---
name: memoria-projeto
description: >
  Salva e retoma o contexto de trabalho de um projeto entre sessões, sem depender do
  /compact: mantém CONTEXTO.md (estado atual, sobrescrito, ≤1 página) + sessoes/AAAA-MM-DD.md
  (diário append-only) na raiz do projeto e garante o ponteiro no CLAUDE.md. Grava ESTADO e
  decisões com porquê — nunca resumo de conversa. TRIGGER modo SALVAR quando o usuário
  disser "salva o contexto", "atualiza a memória do projeto", "vamos fechar por hoje",
  "registra onde paramos", "salva a sessão"; modo RETOMAR quando disser "onde paramos?",
  "retoma o projeto", "me atualiza do projeto", "o que aconteceu nas últimas sessões?".
  NÃO usar para: preferências/fatos pessoais duráveis (isso é a auto-memory do Claude),
  documentação de código/convenções (CLAUDE.md, /init), nem para compactar a conversa.
---

# Memória do Projeto

Substitui o /compact por um handoff de verdade: o que preserva contexto entre sessões não é resumo de conversa — é o ESTADO do projeto (o que está pronto/andando/bloqueado, decisões com porquê, pendências, aprendizados, mapa de artefatos). Dois modos: **SALVAR** (fecha a sessão gravando o estado) e **RETOMAR** (abre a sessão com briefing). Funciona em qualquer projeto.

## Regras duras

1. **Estado, não narrativa.** NUNCA reconte a conversa ("o usuário pediu X, depois discutimos Y..."). Grave o que mudou de estado, as decisões e o que falta. Se o texto parece resumo de chat, está errado — virou um /compact manual, o problema que esta skill existe pra matar.
2. **Nunca grave o que os arquivos/git já mostram** (estrutura de pastas, conteúdo de código, histórico de commits). Redundância envelhece mal e incha o contexto. Grave o que NÃO está escrito em lugar nenhum.
3. **Decisão sem porquê não entra.** "Escolhemos X" é inútil; "escolhemos X em vez de Y porque Z" é o que o /compact mata e esta skill salva.
4. **CONTEXTO.md ≤1 página (~60 linhas), sempre SOBRESCRITO.** Quando crescer, comprima as decisões antigas em 1 linha cada — o detalhe vive no diário. O CONTEXTO é o que toda sessão nova lê; cada linha custa contexto pra sempre.
5. **Datas absolutas** ("2026-07-07"), nunca relativas ("hoje", "semana passada").
6. **Todo salvamento reconfere e recria o ponteiro no CLAUDE.md** do projeto (se o CLAUDE.md não existir, crie um mínimo com o ponteiro). É o que garante que nenhuma sessão futura abra cega.
7. **Nunca invente.** Só entra o que aconteceu de fato na sessão; em dúvida sobre uma decisão ou estado, pergunte ao usuário antes de gravar.
8. **Retomada lê CONTEXTO.md + o último diário, só.** Briefing de ~10 linhas. Nunca reler a história inteira de sessoes/ (ela existe pra consulta pontual, não pra recarga).

## Modo SALVAR

Dispara ao fechar trabalho ("salva o contexto", "vamos fechar por hoje").

### 1. Localizar/criar a estrutura
Na raiz do projeto atual: `CONTEXTO.md`, pasta `sessoes/`, e o ponteiro no `CLAUDE.md`. Primeira vez no projeto? Crie os três (CLAUDE.md mínimo se não existir) usando `references/template-contexto.md`.

### 2. Colher da sessão (o filtro é a regra 1)
Varra a sessão atual e extraia APENAS: o que mudou de estado (pronto/andando/bloqueado), decisões tomadas + porquê, pendências novas ou resolvidas, aprendizados/armadilhas descobertos, artefatos criados/movidos que importam. Em dúvida, pergunte (regra 7).

### 3. Escrever o diário da sessão
`sessoes/AAAA-MM-DD.md` (append se já existir sessão no dia) no formato do template: o que foi feito, decisões + porquê, descobertas, o que ficou pra próxima.

### 4. Reescrever o CONTEXTO.md
SOBRESCREVA seguindo o template: estado atual atualizado, decisões-chave (novas entram, antigas comprimem se passar de 1 página), pendências atualizadas (resolvidas SAEM), aprendizados, mapa de artefatos, link do diário de hoje. Valide contra as regras 1–5 antes de gravar.

### 5. Garantir o ponteiro
Confirme no CLAUDE.md a linha (recrie se sumiu):
`> **Memória do projeto:** leia CONTEXTO.md antes de começar qualquer trabalho. Ao fechar uma sessão de trabalho, atualize-o (skill memoria-projeto).`

### 6. Reportar
3 linhas pro usuário: o que foi gravado, o que saiu (pendências resolvidas), e a pendência nº 1 pra próxima sessão.

## Modo RETOMAR

Dispara ao abrir trabalho ("onde paramos?", "retoma o projeto").

### 1. Ler
`CONTEXTO.md` + o diário mais recente de `sessoes/` (só ele — regra 8). Não existem? Diga que o projeto ainda não tem memória e ofereça criar na primeira gravação.

### 2. Briefing (~10 linhas)
(a) o que é o projeto em 1 linha; (b) estado: pronto / em andamento com onde parou / bloqueado com porquê; (c) as 2–3 decisões que regem o trabalho atual; (d) a pendência nº 1 e o próximo passo sugerido.

### 3. Engatar
Pergunte se começa pela pendência nº 1 ou por outra coisa — e comece.

## Graus de liberdade

- **Fixo**: estrutura de arquivos, template do CONTEXTO.md, regras duras, sobrescrever (nunca acumular) o CONTEXTO, ponteiro no CLAUDE.md.
- **Livre**: granularidade do diário (sessão densa = diário maior, sem limite rígido), julgamento sobre o que é "decisão-chave" vs detalhe, formato do briefing de retomada.

## Ponteiros

- `references/template-contexto.md` — templates do CONTEXTO.md, do diário e do CLAUDE.md mínimo; use no passo 1 e 3–4 do SALVAR.
- `references/exemplos.md` — pares certo/errado; leia antes do passo 2 do SALVAR.
