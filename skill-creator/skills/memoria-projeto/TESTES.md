# Casos de teste — memoria-projeto

(arquivo de desenvolvimento; não instalar)

## Caso 1 — SALVAR em projeto virgem (bootstrap)
**Setup:** pasta de projeto fictícia sem CONTEXTO.md, sem sessoes/, sem CLAUDE.md.
**Input:** "Vamos fechar por hoje, salva o contexto" + resumo da sessão fictícia (criou landing page, decidiu stack, ficou pendência).
**Esperado:** cria CONTEXTO.md (≤1 página, template completo), sessoes/AAAA-MM-DD.md, e CLAUDE.md mínimo com o ponteiro; conteúdo em formato ESTADO (zero narrativa de conversa); decisões com porquê; datas absolutas; reporta em 3 linhas.

## Caso 2 — SALVAR em projeto existente (atualizar sem inchar)
**Setup:** projeto com CONTEXTO.md cheio (com pendências, decisões antigas) + sessoes/ com 2 diários + CLAUDE.md SEM o ponteiro (foi removido).
**Input:** "salva a sessão" + eventos da sessão (2 pendências resolvidas, 1 decisão nova, 1 armadilha descoberta).
**Esperado:** CONTEXTO.md SOBRESCRITO: pendências resolvidas SAEM (não viram "✓ feito"), decisão nova entra com porquê, tamanho continua ≤1 página; novo diário criado; **ponteiro RECRIADO no CLAUDE.md** (regra 6) sem tocar no resto do arquivo.

## Caso 3 — RETOMAR
**Setup:** projeto com CONTEXTO.md + 3 diários em sessoes/.
**Input:** "Onde paramos nesse projeto?"
**Esperado:** lê CONTEXTO.md + APENAS o diário mais recente (regra 8 — não lê os 3); briefing de ~10 linhas (o que é, estado, decisões que regem, pendência nº 1); termina engatando ("começamos pela pendência 1 ou...?").

## Caso 4 — Armadilha: fato pessoal
**Input:** durante um salvamento, o usuário diz "aproveita e registra que eu prefiro sempre ver o plano antes de você executar".
**Esperado:** a skill NÃO grava isso no CONTEXTO.md — explica que preferência pessoal é território da auto-memory (atravessa projetos) e a registra lá (ou oferece registrar), mantendo o CONTEXTO só com estado do projeto (exemplos.md, Erro 5).

## Teste de gatilho
- SALVAR dispara: "salva o contexto", "vamos fechar por hoje", "atualiza a memória do projeto".
- RETOMAR dispara: "onde paramos?", "retoma o projeto", "me atualiza do projeto".
- NÃO dispara: "lembra que eu gosto de X" (auto-memory), "documenta o código" (/init), "compacta a conversa".
