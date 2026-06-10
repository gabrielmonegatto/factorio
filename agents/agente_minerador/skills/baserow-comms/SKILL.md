# Skill: baserow-comms

## O que faz
Envia e registra notificações, alertas ou solicitações de decisão do agente para a tabela central `agent_communications` no Baserow (DB: Factorio, Tabela 1520).

## Quando usar
Sempre que precisar comunicar algo ao superior (Diretor ou Usuário) ao longo ou no fim do ciclo de operação. Substitui o uso de logs avulsos ou de comandos de chat diretos para execuções assíncronas/background, centralizando a observabilidade e permitindo criar uma fila de pendências para o CEO/Diretor responder.

### Categorias de Comunicação:
- `report`: Sumário de conclusão de ciclo (ex: "Mineração concluída: 50 novos vídeos extraídos").
- `alert`: Alertas de erros não-críticos ou problemas temporários em workers (ex: "Falha na transcrição do vídeo X, tentando corrigir").
- `decision_required`: Bloqueio real que necessita de intervenção humana (ex: "Fonte X mudou o layout de HTML. Preciso de novas regras de extração.").
- `info`: Logs informativos gerais para rastreabilidade de eventos.

## Como executar

### Opção 1: Via worker (Método recomendado)
Use a ferramenta de terminal para executar o worker `send_ticket.py`:
```bash
python workers/send_ticket.py --agent <nome_do_agente> --type <report|alert|decision_required|info> --priority <low|medium|high|critical> --message "<mensagem>" --cycle_id "<id_do_ciclo>" --context "<dados_json_ou_texto>"
```

**Exemplo prático:**
```bash
python workers/send_ticket.py --agent agente_minerador --type report --priority medium --message "Ciclo concluído: 15 vídeos novos importados." --cycle_id "run-miner-102"
```

### Opção 2: Via API Baserow Diretamente (Alternativa)
- **Método:** `POST`
- **URL:** `http://factorio.io/api/database/rows/table/1520/?user_field_names=true`
- **Headers:**
  - `Authorization: Token <BASEROW_TOKEN>` (configurado no `.env`)
  - `Content-Type: application/json`
- **JSON Payload:**
  ```json
  {
    "agent": "agente_minerador",
    "type": "report",
    "priority": "medium",
    "message": "Mensagem descritiva do ticket",
    "context": "Contexto técnico em string/JSON",
    "status": "pending",
    "cycle_id": "run-miner-102",
    "created_at": "2026-05-19T11:40:00"
  }
  ```

## Saída esperada (via worker)
```
✅ Ticket enviado com sucesso! ID: 2
```

## Após executar
Continue com a execução do ciclo ou encerre o processo normalmente. O Diretor de Operações ou o Usuário lerão e resolverão os tickets diretamente pela tabela do Baserow.
