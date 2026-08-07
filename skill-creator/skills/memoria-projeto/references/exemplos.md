# Exemplos: certo vs. errado

Um par por modo de falha. Leia antes de colher o conteúdo da sessão (passo 2 do SALVAR).

## Erro 1: Resumo de conversa em vez de estado

❌ **Errado:**
> "O usuário pediu pra criar um quiz, depois discutimos qual framework usar, aí eu sugeri o Xisto e ele concordou. Em seguida montamos o blueprint e ele pediu pra colocar no Quiz Maker. Conversamos sobre os depoimentos..."

✅ **Certo:**
> "🔄 **Em andamento:** quiz 'Raio-X da Contratação PJ' montado no Quiz Maker (#56, draft, 28 etapas) — falta: validar fórmula de exposição com a Juliana, trocar depoimentos placeholder, configurar pixel."

**Por quê:** narrativa de conversa é o que o /compact já faz — e envelhece instantaneamente (quem leu não sabe o que FAZER). Estado diz onde está e o que falta; a próxima sessão age em 30 segundos.

## Erro 2: Decisão sem porquê

❌ **Errado:**
> "Decidimos usar o framework Xisto pro quiz."

✅ **Certo:**
> "[2026-07-05] Quiz da Juliana usa framework Xisto (não SPIN/Ask) — porque R$37 é compra por impulso e o produto permite personalização por diagnóstico de risco; SPIN mataria o ímpeto, Ask é pra segmentar mercado."

**Por quê:** sem o porquê, a próxima sessão re-litiga a decisão (ou pior: desfaz sem saber). O porquê é exatamente a camada que se perde na compactação — é o ativo mais valioso do CONTEXTO.

## Erro 3: Gravar o que o git/arquivos já mostram

❌ **Errado:**
> "O projeto tem as pastas skills/, livros/, destilados/, entrevistas/. O SKILL.md do quiz-framework-xisto tem 68 linhas e contém as regras duras 1 a 10, que são: 1) Cheque o formato..."

✅ **Certo:**
> "Mapa de artefatos: `outputs/quiz-blueprint-raio-x-contratacao-pj.md` — blueprint aprovado que alimenta a leva de ads (próxima pendência)."

**Por quê:** o que está em arquivo se lê do arquivo — cópia no CONTEXTO desatualiza na primeira edição e vira mentira. O CONTEXTO aponta ONDE está e POR QUE importa, nunca duplica conteúdo.

## Erro 4: CONTEXTO.md que só cresce

❌ **Errado:** CONTEXTO com 240 linhas: 14 decisões detalhadas de 3 semanas atrás, pendências marcadas "✓ feito" acumulando, histórico de cada sessão colado no fim.

✅ **Certo:** CONTEXTO com ~50 linhas: decisões antigas comprimidas em 1 linha cada ("[2026-07-04] Família de quiz = 3 frameworks com desambiguação cruzada — detalhe em sessoes/2026-07-04.md"), pendências resolvidas REMOVIDAS, história vivendo em sessoes/.

**Por quê:** o CONTEXTO.md é lido por TODA sessão futura — cada linha custa contexto pra sempre. Ele é um snapshot, não um livro-razão; o diário append-only é quem guarda a história. Sobrescrever e comprimir é o que o mantém útil.

## Erro 5: Guardar fato pessoal do usuário no CONTEXTO do projeto

❌ **Errado:**
> "Aprendizados: o Pedro prefere respostas em português e gosta de aprovar planos antes da execução."

✅ **Certo:** isso NÃO entra no CONTEXTO.md — é fato durável sobre o usuário, território da auto-memory do Claude (que carrega em toda sessão de qualquer projeto). No CONTEXTO entra só o que é DESTE projeto: "Aprendizado: o InLead não expõe cupom automático via API — cupom do quiz #56 foi configurado manualmente."

**Por quê:** cada memória no lugar certo — preferências do usuário na auto-memory (atravessam projetos), estado de trabalho no CONTEXTO (morre com o projeto). Misturar duplica e confunde as duas camadas.
