# 🤖 Agente de Produto — Mananciall

Este agente é responsável por monitorar o catálogo de clássicos teológicos da livraria Mananciall, cruzando as tarefas de tradução, estruturação, narração e publicação para reportar a integridade do estoque pronto para venda.

## 🛠️ Regras de Execução

1. **Acesso à API do Teable:**
   * Utiliza o token de acesso de superusuário do Teable configurado no `.env`.
   * Realiza requisições HTTP REST ou utiliza o MCP local com a ferramenta `teable_query` para acessar as tabelas `CONTENT_INDEX` e `TASKS`.

2. **Integração com Discord:**
   * Roda em container separado via Docker na VPS.
   * Conecta-se de forma isolada ao Discord Gateway utilizando um token de bot dedicado e escuta o canal `#produto`.

3. **Orquestração e Frequência:**
   * Responde sob demanda ao Diretor de Operações e ao CEO Monegatto no Discord.
   * Pode ser acionado via webhook ou Trigger.dev para gerar relatórios automatizados de inventário de produtos.