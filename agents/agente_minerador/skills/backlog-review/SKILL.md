# Skill: backlog-review

## O que faz
Consulta a tabela `taskflows` no Baserow e retorna o estado atual do backlog de mineração.

## Quando usar
Sempre que precisar saber o que tem no pipeline, quantas tarefas estão em cada status, ou qual é a próxima prioridade.

## Como executar

### Opção 1: via worker (preferencial)
```
execute("python workers/check_backlog.py")
```
Retorna contagem por status e lista das tarefas de alta prioridade.

### Opção 2: via API Baserow diretamente
- URL: `http://factorio.io/api/database/rows/table/623/`
- Requer `BASEROW_TOKEN` e `BASEROW_URL` do `.env`.

## Saída esperada
```
Backlog: 5 tarefas
In Progress: 2 tarefas
Failed: 1 tarefa
Done: 3 tarefas

Próxima prioridade Alta:
- [ID 3] Revisar pipeline Discovery → Processing (Mineração)
```

## Após executar
Com os dados em mãos, decida:
- Se há tarefas `Failed` → investigue antes de iniciar novas
- Se há tarefas `Backlog` com prioridade Alta → despache worker correspondente
- Se tudo `Done` → reporte ao CEO via `message_user`
