# Exemplos: certo vs. errado

Todos os casos vêm da migração real do ZOAC (2026-07-10): `zoac-front` e `zoac-backend` movidas para dentro de `/Volumes/KINGSTON/claude/Zoac/`.

## Erro 1: Mover só a pasta e esquecer o ~/.claude/projects

❌ **Errado:**
```bash
mv /Volumes/KINGSTON/claude/zoac-front /Volumes/KINGSTON/claude/Zoac/
# "pronto, movido!"
```

✅ **Certo:**
```bash
mv /Volumes/KINGSTON/claude/zoac-front /Volumes/KINGSTON/claude/Zoac/
mv ~/.claude/projects/-Volumes-KINGSTON-claude-zoac-front \
   ~/.claude/projects/-Volumes-KINGSTON-claude-Zoac-zoac-front
```

**Por quê:** o `/resume` procura o diretório cujo nome codifica o cwd atual. Sem o segundo `mv`, o Claude cria um diretório novo vazio e o histórico "some" (está lá, mas órfão).

## Erro 2: sed no ~/.claude.json

❌ **Errado:**
```bash
sed -i '' 's|/claude/zoac-front|/claude/Zoac/zoac-front|g' ~/.claude.json
```

✅ **Certo:**
```bash
python3 scripts/rename_claude_json_key.py \
  /Volumes/KINGSTON/claude/zoac-front /Volumes/KINGSTON/claude/Zoac/zoac-front
```

**Por quê:** o `~/.claude.json` guarda TODA a config do Claude Code (todos os projetos, MCPs, histórico de prompts). sed não entende escapes JSON — o caminho pode aparecer dentro de strings escapadas ou de valores que não são a chave. Um byte errado e o Claude Code perde a config inteira. Python renomeia SÓ a chave e grava atomicamente.

## Erro 3: Substituir o nome curto em vez do caminho absoluto

❌ **Errado:**
```bash
sed -i '' 's|zoac-front|Zoac/zoac-front|g' sessao.jsonl
```

✅ **Certo:**
```bash
LC_ALL=C sed -i '' 's|/Volumes/KINGSTON/claude/zoac-front|/Volumes/KINGSTON/claude/Zoac/zoac-front|g' sessao.jsonl
```

**Por quê:** "zoac-front" solto aparece em nomes de repo GitHub (`pedrovisao/zoac-front`), URLs, usernames de FTP (`zoac-front`) e texto de conversa — nada disso deve mudar. Só o caminho absoluto completo identifica sem ambiguidade o que é caminho local.

## Erro 4: Ignorar colisão case-insensitive

❌ **Errado:** criar `Zoac` e assumir que `-Volumes-KINGSTON-claude-Zoac` é um diretório novo, sem checar.

✅ **Certo:**
```bash
ls ~/.claude/projects/ | grep -ix -- "-Volumes-KINGSTON-claude-Zoac"
# achou "-Volumes-KINGSTON-claude-zoac" (projeto antigo!) → arquivar antes:
mkdir -p ~/.claude/projects-archive && mv ~/.claude/projects/-Volumes-KINGSTON-claude-zoac ~/.claude/projects-archive/
```

**Por quê:** o APFS do macOS é case-insensitive: pro filesystem, `-...-Zoac` e `-...-zoac` são o MESMO diretório. No caso real, rodar `claude` na raiz `Zoac` teria caído no histórico do projeto `zoac` antigo e carregado uma memória enganosa ("esta pasta é a produção antiga — não alterar").

## Erro 5: Esquecer memórias de OUTROS projetos

❌ **Errado:** atualizar só a memória do projeto movido.

✅ **Certo:**
```bash
grep -rl "/Volumes/KINGSTON/claude/zoac-backend" ~/.claude/projects/*/memory/
# achou também a memória do projeto zoac ANTIGO apontando pro backend → corrigir lá também
```

**Por quê:** memórias apontam umas para as outras entre projetos. No caso real, a memória do projeto `zoac` dizia "o trabalho ativo agora é em /Volumes/KINGSTON/claude/zoac-backend" — se não fosse corrigida, qualquer sessão futura naquele projeto mandaria o Claude para uma pasta inexistente.
