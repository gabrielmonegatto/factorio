# Entrevista — mover-projeto (2026-07-10)

Contexto: a entrevista não foi um questionário — a skill nasceu de uma execução real feita nesta data (mover `zoac-front` e `zoac-backend` para dentro de `/Volumes/KINGSTON/claude/Zoac/`). Os blocos 1, 3 e 4 foram extraídos dessa execução; os blocos 2, 6 e 7 foram confirmados com o Pedro via perguntas diretas.

## Bloco 1 — O Job
- Input: caminho(s) de projeto atual(is) + destino desejado (mover para dentro de pasta nova, renomear, agrupar várias pastas).
- Output: pastas no lugar novo com TUDO que o Claude Code atrela ao caminho absoluto preservado — `/resume` mostra as conversas antigas, memória automática carrega, configs de projeto seguem valendo.
- "Pronto" = usuário entra na pasta nova, roda `claude`, dá `/resume` e vê o histórico; memória carrega; zero referências ao caminho antigo sobrando.
- Exemplo real: a migração do ZOAC de 2026-07-10 (ver sessão desta data na pasta Zoac).

## Bloco 2 — Gatilho (frases literais do Pedro)
- "mover projeto" / "mover essas pastas para dentro de X"
- "mudar o local do projeto" / "mudar a pasta do projeto"
- "renomear a pasta do projeto"
- "agrupar projetos" (juntar pastas dentro de uma pasta única)
- NÃO dispara para: mover arquivos soltos dentro de um projeto, migração de servidor/banco/hospedagem, mover repos entre contas GitHub.

## Bloco 3 — Barra de qualidade
- Excelente = o usuário não percebe que houve mudança: `/resume` funciona, memória carrega, git intacto, configs preservadas, e a varredura externa achou referências que ele nem lembrava (launchd, cron, memórias de outros projetos).
- Rejeição mesmo com 8/10: se o histórico de conversas não aparecer no `/resume` da pasta nova. É a razão de existir da skill.

## Bloco 4 — Modos de falha (da execução real)
1. Mover só a pasta e esquecer `~/.claude/projects/` → histórico "some".
2. Editar `~/.claude.json` com sed → risco de corromper a config inteira (JSON gigante, tudo do Claude Code está nele).
3. Substituir o nome curto da pasta em vez do caminho absoluto → corrompe texto não relacionado (nomes de repo, URLs).
4. Colisão case-insensitive no APFS: `-...-Zoac` e `-...-zoac` são o MESMO diretório para o filesystem — no caso real, o histórico antigo de `zoac` teve que ser arquivado antes de usar a raiz `Zoac`.
5. Esquecer memórias de OUTROS projetos que citam o caminho movido (no caso real, a memória do projeto `zoac` antigo apontava pro `zoac-backend`).
6. Executar com sessão do Claude aberta na pasta → a sessão regrava o caminho antigo ao fechar.

## Bloco 5 — Fontes de expertise
- A própria execução de 2026-07-10 (plano em `~/.claude/plans/eu-tenho-as-pastas-prancy-dewdrop.md`).

## Bloco 6 — Graus de liberdade
- SEMPRE igual: backup antes de tocar em `~/.claude`; mapear → mostrar plano → aprovar → executar; python (nunca sed) no `~/.claude.json`; verificação final com checklist.
- Liberdade: ordem da varredura, formato do relatório do mapa, como corrigir referências externas achadas (propor caso a caso).

## Bloco 7 — Contexto de execução
- Só shell + python3 locais. Nada de MCP/API.
- Escopo amplo confirmado pelo Pedro: além do Claude Code, varrer LaunchAgents, crontab, `~/.claude/settings.json`, e memórias/projetos vizinhos por referências ao caminho antigo.
- Comportamento confirmado: mapear → mostrar plano → executar (não executar às cegas).

## Bloco 8 — Output
- Relatório na conversa: mapa do que existe atrelado, plano, execução, checklist de verificação. Sem arquivo entregável (a entrega é o estado do sistema).
