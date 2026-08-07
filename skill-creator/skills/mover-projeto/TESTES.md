# Testes — mover-projeto

## Caso 1 — Agrupar (o caso real de origem)
**Input:** "eu tenho as pastas `proj-a` e `proj-b` em `/Users/x/dev/`, quero as duas dentro de uma pasta nova `/Users/x/dev/Grupo`, preservando o /resume e a memória"
**Output esperado:** plano que cubra TODAS as 6 frentes: (1) mv das pastas; (2) mv dos diretórios codificados em ~/.claude/projects; (3) sed do caminho absoluto nos .jsonl; (4) renomear chave no ~/.claude.json via python; (5) grep de memórias de TODOS os projetos; (6) varredura externa (launchd/cron/settings). Mais: backup antes, checagem de colisão case-insensitive, aviso sobre sessões abertas, checklist de verificação.
**Reprova se:** faltar qualquer uma das frentes 2–4, propuser sed no ~/.claude.json, ou substituir nome curto da pasta.

## Caso 2 — Renomear pasta
**Input:** "renomeia a pasta do projeto `/Users/x/dev/meuapp` pra `/Users/x/dev/meu-app`"
**Output esperado:** mesmo procedimento com uma pasta só; a checagem de colisão case-insensitive é obrigatória (meuapp vs meu-app não colide, mas a checagem deve aparecer).
**Reprova se:** tratar renomear como caso diferente de mover (é o mesmo procedimento).

## Caso 3 — Gatilho
**Devem disparar:** "quero mover o projeto X pra dentro da pasta Y"; "mudar o local do projeto"; "renomear a pasta do projeto"; "agrupar esses projetos numa pasta única".
**NÃO devem disparar:** "mover esse arquivo pra outra pasta" (operação dentro do projeto); "migrar o projeto pro MySQL" (migração de infra); "mover o repo pra outra conta do GitHub".

## Resultados (2026-07-10)
- Script `rename_claude_json_key.py`: testado contra um ~/.claude.json sintético (renomeia, recusa colisão, no-op se chave não existe) — passou.
- Caso 1: subagente com o SKILL.md produziu plano cobrindo as 6 frentes + backup + colisão — passou.
- Caso 3: subagente classificou 7/7 frases corretamente — passou.
