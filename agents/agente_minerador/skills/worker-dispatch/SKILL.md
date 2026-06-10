# Skill: worker-dispatch

## O que faz
Aciona os workers Python corretos para cada etapa do pipeline de mineração.

## Regra de ouro
**Você NUNCA pede para o usuário rodar um script.** Você usa `execute` diretamente. Se o script não existir, você o cria com `write_file` e então executa.

## Como usar o `execute`

```
execute("python workers/NOME_DO_WORKER.py")
execute("python workers/NOME_DO_WORKER.py --arg valor")
```

O `execute` roda no diretório raiz do agente. Os workers estão em `workers/`.

## Mapa de Workers por Etapa do Pipeline

| Etapa | Worker | Comando |
|---|---|---|
| Verificar backlog | `check_backlog.py` | `execute("python workers/check_backlog.py")` |
| Chamar LLM (OpenRouter) | `call_llm.py` | `execute("python C:/Users/Monegatto/Desktop/EternalL/call_llm.py --prompt \"...\"")` |
| Extração de conteúdo | `extract_content.py` | `execute("python workers/extract_content.py --batch 50")` |
| Limpeza | `clean_content.py` | `execute("python workers/clean_content.py")` |
| Atualizar status Baserow | `update_status.py` | `execute("python workers/update_status.py --id ROW_ID --status done")` |

## Se o worker não existir
1. Crie com `write_file("workers/novo_worker.py", conteudo)`
2. Execute com `execute("python workers/novo_worker.py")`
3. Registre a criação em `memories/AGENTS.md`

## Fluxo padrão
```
1. execute("python workers/check_backlog.py")         → vê o estado atual
2. execute("python workers/extract_content.py")       → extrai o próximo lote
3. execute("python workers/update_status.py --...")   → atualiza o Baserow
4. message_user("Ciclo concluído: X itens processados, Y erros.")
```
