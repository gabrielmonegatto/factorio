---
name: mover-projeto
description: >
  Move, renomeia ou agrupa pastas de projeto preservando tudo que o Claude Code
  atrela ao caminho absoluto: histórico de conversas (/resume), memória automática,
  configurações no ~/.claude.json e referências externas (launchd, cron, memórias de
  outros projetos). Mapeia o que existe, mostra o plano, faz backup e executa.
  TRIGGER quando o usuário pedir "mover projeto", "mover essas pastas para dentro de",
  "mudar o local do projeto", "mudar a pasta do projeto", "renomear a pasta do projeto",
  "agrupar projetos" numa pasta única. NÃO usar para mover arquivos dentro de um
  projeto, para migração de servidor/banco/hospedagem, nem para transferir
  repositório entre contas do GitHub (o caminho local não muda).
---

# Mover Projeto

Muda o caminho de uma pasta de projeto sem perder nada do Claude Code: depois da mudança, `/resume` na pasta nova mostra as conversas antigas e a memória automática carrega. A entrega é o estado do sistema + um relatório (mapa → plano → execução → verificação) na conversa.

## Como o Claude Code atrela dados ao caminho

Cada projeto tem um diretório em `~/.claude/projects/` cujo nome é o caminho absoluto com todo caractere não-alfanumérico virando `-` (ex.: `/Volumes/KINGSTON/claude/zoac-front` → `-Volumes-KINGSTON-claude-zoac-front`). Dentro: sessões `.jsonl` (com campo `cwd`), subpastas de subagentes e `memory/`. Além disso, `~/.claude.json` tem uma chave por caminho absoluto em `projects{}` (trust, onboarding, mcpServers do projeto).

## Regras duras

1. **NUNCA edite `~/.claude.json` com sed/regex** — é um JSON gigante com TODA a config do Claude Code; um escape errado corrompe tudo. Sempre python: `json.load` → renomear chave → `json.dump` em `.tmp` → `os.replace`.
2. **SEMPRE backup antes de tocar em `~/.claude`**: `cp -R` dos diretórios de projeto afetados + `cp ~/.claude.json`. Sem backup, um erro no meio é irrecuperável.
3. **Substitua sempre o caminho absoluto completo, nunca o nome curto da pasta** — "zoac-front" solto aparece em nomes de repo, URLs e textos que não devem mudar. E com guarda de fronteira: `/claude/foo` casa o prefixo de `/claude/foo-bar` — em python use regex `re.escape(old) + r'(?![\w.-])'`; em sed, confira antes se existe pasta irmã com o mesmo prefixo.
3b. **`~/.claude.json` guarda caminhos FORA de `projects{}`** — `githubRepoPaths` (repo → caminho local) e `mcpServers` (global e dentro de cada projeto) têm valores com caminho absoluto. Varra o JSON INTEIRO (walk recursivo em python) atrás do caminho antigo, não só as chaves de projeto. E chaves de projeto existem também para SUBpastas (`obsidian/mybrain`, `ad-creator/projetos/gedasio`): busque com `startswith(old + '/')`, nunca só igualdade.
3c. **Serviço launchd rodando na pasta = parar antes, religar depois.** Sequência: `launchctl bootout gui/501/<label>` → mv → corrigir launcher → `launchctl bootstrap gui/501 <plist>` (se der "Input/output error", aguarde 3s e repita). Mover com processo vivo + KeepAlive = crash-loop. Os launchers em `~/claude-launch/*.sh` usam `$VOL/claude/...` na linha do `cd` — sed por caminho absoluto NÃO pega essa linha; use o padrão relativo `claude/<pasta>` (que não casa `claude/<outra>/<pasta>`).
4. **Cheque colisão case-insensitive antes de renomear** — no APFS/macOS, `-...-Zoac` e `-...-zoac` são o MESMO diretório. Se o nome novo colide com um diretório de outro projeto (mesmo diferindo só em maiúsculas), resolva antes (arquivar o antigo em `~/.claude/projects-archive/` ou avisar o usuário).
5. **Nenhuma sessão do Claude Code aberta na pasta durante a mudança** — sessão aberta regrava o caminho antigo no `~/.claude.json` e no diretório de projeto ao continuar. Confirme com o usuário antes de executar.
6. **Mapear antes de substituir** — todo replace é precedido de um grep que mostra ONDE o caminho aparece. Nunca rode substituição às cegas.
7. **Verifique JSON válido depois de mexer em `.jsonl`** — um sed que quebre uma linha mata a sessão inteira no `/resume`.

## Workflow

### 1. Mapear
Para cada pasta a mover, com o caminho antigo `$OLD` e o novo `$NEW`:
- `~/.claude/projects/`: existe o diretório codificado? E de SUBpastas (`<codificado>-*`)? Quantas sessões/memórias?
- `~/.claude.json`: chave `projects["$OLD"]` E chaves `startswith("$OLD/")` E ocorrências do caminho em QUALQUER valor (walk recursivo: `githubRepoPaths`, `mcpServers` global e por projeto). Python, não grep.
- Dentro dos `.jsonl` do projeto (inclusive subpastas de subagente): `grep -c "$OLD"`.
- Memórias de TODOS os projetos: `grep -rl "$OLD" ~/.claude/projects/*/memory/` — e também as formas ANTIGAS do caminho (`~/claude/...`, `/Users/.../claude/...`) que memórias velhas ainda citam.
- Dentro do próprio projeto: `grep -rl "$OLD"` (configs, scripts, `.claude/`, `.mcp.json`) excluindo `node_modules/.git`.
- Varredura externa: `~/.claude/settings.json` (hooks!), `~/.claude/commands/`, `~/.claude/agents/`, `~/.claude/skills/`, `~/claude-launch/*.sh` (launchers com `$VOL` — regra 3c), `~/Library/LaunchAgents/*.plist`, `launchctl list` (jobs rodando DA pasta), `crontab -l`, `.mcp.json` de outros projetos, e vizinhos que hardcodam o caminho (bots são os campeões: `main.py`, `topics.json`, `bot.mjs`).
- Processos vivos: `ps aux | grep "$OLD"` + sessões do Claude com cwd na pasta (regra 5).
- Colisão (regra 4): `ls ~/.claude/projects/ | grep -ix "<nome-novo-codificado>"`. Atenção: `foo-site` e `foo/site` codificam para o MESMO nome — às vezes o rename do diretório é desnecessário, só o conteúdo muda.

**Output verificável:** tabela do que existe atrelado + plano de execução. Mostre ao usuário e espere aprovação (a menos que ele já tenha pedido execução direta).

### 2. Backup
`cp -R` dos diretórios de projeto afetados + `~/.claude.json` para o scratchpad (ou pasta que o usuário indicar). Informe o caminho do backup.

### 3. Executar (nesta ordem)
1. `mkdir` destino se preciso; `mv` da(s) pasta(s).
2. `mv` do diretório em `~/.claude/projects/` para o nome novo codificado.
3. Nos `.jsonl` (os que o grep do passo 1 apontou): `LC_ALL=C sed -i '' 's|$OLD|$NEW|g'`.
4. `~/.claude.json`: renomear a chave via `scripts/rename_claude_json_key.py "$OLD" "$NEW"` (regra 1). Se não houver chave, siga em frente — o trust dialog vai aparecer uma vez, normal.
5. Memórias e arquivos do projeto que o grep apontou: mesmo sed do caminho absoluto.
6. Referências externas achadas (launchd, cron, vizinhos): corrigir uma a uma, avisando o que mudou.

### 4. Verificar
- `ls ~/.claude/projects/` mostra o diretório novo; `grep -r "$OLD"` no diretório novo retorna zero.
- `.jsonl` continua JSON válido linha a linha (python).
- Se for repo git: `git -C $NEW status` funciona.
- Se havia serviço launchd: job voltou (`launchctl print` = running) e o processo tem cwd na pasta NOVA (`lsof -p <pid> -d cwd`).
- **Varredura de órfãos** (pega o que o mapa perdeu): extraia toda referência `/Volumes/.../claude/...` das superfícies vivas (`grep -rIohE '<raiz>/[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)?'` na raiz dos projetos — excluindo node_modules/.git/.venv/backups — mais `~/claude-launch`, `~/.claude/{commands,agents,skills,settings.json}`, `~/.claude.json`) e teste `os.path.exists` em cada uma. Referência quebrada = apontamento que o move deixou para trás. (Exceções legítimas: exemplos históricos em docs, backups.)
- Peça ao usuário o teste final: entrar na pasta nova, `claude`, `/resume` → conversa antiga aparece.

**Output verificável:** checklist com os 4 itens acima + o caminho do backup.

## Graus de liberdade

- **Fixo:** ordem mapear → plano → backup → executar → verificar; python no `~/.claude.json`; substituição só de caminho absoluto; checagem de colisão.
- **Livre:** formato do relatório; como corrigir cada referência externa (propor caso a caso); onde guardar o backup.

## Ponteiros

- `references/exemplos.md` — pares certo/errado dos 5 modos de falha; leia antes de executar o passo 3.
- `scripts/rename_claude_json_key.py` — renomeia a chave de projeto no `~/.claude.json` com segurança.
