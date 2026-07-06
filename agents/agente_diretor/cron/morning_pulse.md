# Morning Pulse — Ciclo Diário da Fábrica

schedule: "0 9 * * *"

## Instruções

Execute o protocolo matinal completo:

1. Rode `workers/factory_summary.py` e analise o JSON:
   - Total de tasks por status (Pendente / Em Processamento / Concluído)
   - Top projetos com mais pendências
   - Projetos Em Processamento que podem estar travados

2. Consulte `workers/knowledge_search.py --query "gargalo fabrica"` para recuperar contexto histórico.

3. Identifique ações necessárias:
   - Se há projetos com tradução concluída mas narração pendente → acione `translate-content` ou próxima etapa
   - Se há tasks Em Processamento sem progresso recente → diagnostique e acione novamente
   - Se Spurgeon (channels) tem menos de 10 tasks Em Processamento → verificar pipeline

4. Execute as ações identificadas via `workers/trigger_job.py`.

5. Registre o ciclo: `workers/journal_write.py --agent diretor --type observation --summary "Pulse matinal: [resumo breve]"`

6. Envie relatório ao CEO via `message_user` com:
   - Estado geral (verde / amarelo / vermelho)
   - Top 3 projetos mais ativos
   - Ações tomadas hoje
   - Próximos marcos esperados
