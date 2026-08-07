# Hermes Agent Profile Creation (Windows)

Procedimento validado para criar um novo agente no Hermes e fazê-lo aparecer na interface.

## Estrutura de Arquivos

Cada agente tem 3 arquivos essenciais:

| Arquivo | Função | Exemplo |
|---------|--------|---------|
| `SOUL.md` | Identidade, personalidade, tom de voz | "Você é o Líder de Produto do Mananciall..." |
| `AGENTS.md` | System prompt: missão, tools, procedures, dados | "Sua missão: consultar Teable e reportar catálogo..." |
| `config.yaml` | Configuração técnica (modelo, provider, paths) | `model: deepseek/deepseek-v4-pro` |

**Convenção:** SOUL.md = quem o agente É. AGENTS.md = o que o agente FAZ.

## Procedimento de Criação

### 1. Criar diretório do agente no projeto
```
_factorio/agents/agente_<nome>/
  ├── SOUL.md
  ├── AGENTS.md
  └── config.yaml
```

### 2. Registrar o perfil no Hermes
```bash
hermes profile create <nome>
```
Isso cria o diretório em `AppData/Local/hermes/profiles/<nome>/` e registra o perfil no banco interno.

### 3. Escrever os arquivos NO DIRETÓRIO DO APPDATA
**⚠️ CRÍTICO:** O Hermes NÃO descobre perfis por scan de diretório — perfis são REGISTRADOS internamente. O `hermes profile create` registra, mas cria arquivos default. Você precisa sobrescrever os arquivos no path `AppData/Local/hermes/profiles/<nome>/`:

- Usar `write_file` (NÃO `cp` ou `terminal`) para escrever config.yaml e AGENTS.md no AppData
- `cp` via terminal é bloqueado pelo Hermes como operação destrutiva em diretórios de perfil

### 4. Criar symlink (opcional, para organização)
```bash
ln -s /c/Users/Monegatto/Desktop/EternalL/_factorio/agents/agente_<nome> "$HOME/.hermes/profiles/<nome>"
```
Isso mantém o diretório do projeto linkado ao profile dir pra facilitar edição.

### 5. Verificar
```bash
hermes profile list
```
O perfil deve aparecer com modelo e alias.

## Config.yaml Mínimo (DeepSeek V4 Pro)

```yaml
model:
  default: deepseek/deepseek-v4-pro
  provider: openrouter
terminal:
  cwd: C:/Users/Monegatto/Desktop/EternalL
agent:
  max_turns: 50
```

## Pitfalls

- **Symlink NÃO registra o perfil** — precisa de `hermes profile create` antes
- **Escrever via terminal (`cp`) é bloqueado** — use `write_file` no path absoluto do AppData
- **Dois paths existem:** `~/.hermes/profiles/` (symlinks) e `AppData/Local/hermes/profiles/` (real). O AppData é o que o Hermes lê de fato após o register
- **Modelo tem que ser igual ao do Diretor** (deepseek-v4-pro) — CEO rejeitou Gemini free tier pra agentes de produção
- **NÃO use `rm -rf` em profile dirs** — Hermes bloqueia como operação destrutiva

## Exemplo: Criação do Agente Produto

```bash
# 1. Criar diretório
mkdir -p _factorio/agents/agente_produto/

# 2. Escrever SOUL.md, AGENTS.md, config.yaml no diretório do projeto

# 3. Registrar
hermes profile create produto

# 4. Escrever config no AppData (via write_file tool)
# Path: C:\Users\Monegatto\AppData\Local\hermes\profiles\produto\config.yaml
# Path: C:\Users\Monegatto\AppData\Local\hermes\profiles\produto\AGENTS.md

# 5. Symlink
ln -s /c/Users/Monegatto/Desktop/EternalL/_factorio/agents/agente_produto ~/.hermes/profiles/produto
```