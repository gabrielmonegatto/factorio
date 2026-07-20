> ⚠️ **Documento da era 1.0 (pré-redesenho).** Infra, URLs e portas continuam válidas, mas o modelo de agentes descrito aqui (AgentMemory, multi-bot Discord, regras de comportamento de agentes) foi APOSENTADO — ver `01_MASTERPLAN.md` (D4) e `05_LEGACY_TRANSITION.md`. Reescrita completa: roadmap F1.8. Movido da raiz do EternalL em 20/07/2026.

# 🧭 STACK.md — Manual de Infraestrutura e Stack (EternalL Holding)

Este documento descreve a infraestrutura da fábrica de negócios automatizada (**Factorio**), explicando a transição do ambiente local para a VPS, o papel de cada serviço, suas conexões e como novos agentes de IA devem se comportar e se conectar.

---

## 🚀 A Transição: De Local para VPS
Antes, a operação rodava de forma fragmentada na máquina Windows local (Teable local, Caddy local, ChromaDB local). 
Agora, **toda a infraestrutura de produção roda na VPS** com IP público `187.127.44.153` sob o domínio `markeologia.com.br`, gerenciada por containers Docker e protegida por SSL automático via Caddy e Cloudflare.

---

## 🌐 URLs, Subdomínios e Portas Internas

| Serviço | URL Pública | Porta Interna Docker | Descrição |
| :--- | :--- | :--- | :--- |
| **Teable** | `https://db.markeologia.com.br` | `factorio_teable:3000` | Banco de Dados relacional corporativo (estilo planilha). |
| **AgentMemory API** | `https://memory.markeologia.com.br` | `factorio_agent_memory:3111` | API REST de memórias semânticas persistentes. |
| **AgentMemory Streams** | — | `factorio_agent_memory:3112` | WebSocket para streams em tempo real. |
| **Memory Viewer** | `https://memory-viewer.markeologia.com.br` | `factorio_agent_memory:3113` | Painel gráfico de visualização das memórias. |
| **Wiki EternalL** | `https://wiki.markeologia.com.br` | `outline_holding:3000` | Outline Wiki da Holding (Documentação e SOPs). |
| **Wiki Br4nds** | `https://wiki-br4nds.markeologia.com.br` | `outline_br4nds:3000` | Outline Wiki da marca Br4nds (Estratégias de produto). |
| **MinIO Console** | `http://187.127.44.153:9001` | `outline_minio:9001` | Painel visual de armazenamento de objetos S3 local. |
| **Postgres (Teable)** | — | `factorio_teable_db:5432` | Banco físico do Teable (porta mapeada no host: `42345`). |

---

## 🛠️ Detalhamento dos Componentes

### 1. Caddy (Proxy Reverso)
O Caddy é o cérebro de rede na VPS. Ele gerencia os certificados SSL automáticos da Let's Encrypt e roteia o tráfego dos subdomínios para os containers corretos.
> [!IMPORTANT]
> **Multiplexação de WebSockets:**
> O Caddy está configurado para inspecionar cabeçalhos de conexão. Conexões normais de API e do Viewer vão para as portas `3111` e `3113`. Quando o navegador tenta abrir um WebSocket (`wss://`), o Caddy redireciona automaticamente para a porta de Streams `3112` do AgentMemory, o que faz o status do painel ficar **`LIVE`** (verde).
> Ele também gerencia cabeçalhos de **CORS** para permitir que o Viewer carregado de `memory-viewer` faça chamadas AJAX seguras para a API de `memory`.

### 2. Teable (Banco de Dados Corporativo)
Substituiu o Baserow antigo. Centraliza tabelas de inteligência, finanças, mídias e progresso.
* **Tabela `tools` (ID `tblsLfGpdU5kynWoUUN`):** Catálogo unificado de comandos de console, APIs de terceiros e scripts executáveis da holding.
* **Tabela `CONTENT_INDEX` (ID `tblD7Kxoc7gFTgEWoWo`):** Inventário de livros clássicos teológicos da marca Mananciall.
* **Tabela `TASKS` (ID `tblVzN1Eo8tfk7GX2CJ`):** Filas de tarefas, progresso e status do pipeline técnico.
* **Token de API Corporativo:** `teable_accLa1wPXZZgOLLcX0t_Q8N1AUB7+EF26V3SJsYvKWaAXOT47+LrKZxLK+QJiQE=` (Full Access de Superusuário).

### 3. AgentMemory (Colmeia de Conhecimento)
Base de dados semântica (SQLite + ChromaDB) que armazena memórias duradouras da holding.
* **Chave de Acesso (Bearer Token):** `factorio_secret`
* Os agentes de IA se conectam a ela para registrar fatos importantes, credenciais geradas, decisões de design e tarefas executadas.
* O painel pode ser acessado em `https://memory-viewer.markeologia.com.br` informando a chave `factorio_secret`.

### 4. Outline Wiki (Holding & Br4nds)
Plataforma de documentação rica e integrada para documentar processos e centralizar conhecimentos de negócio.
* **Google OAuth:** A autenticação é integrada ao Google Client ID da holding.
* **Storage:** Utiliza o MinIO local para salvar uploads e imagens das páginas de forma 100% autônoma.

### 5. MinIO Object Storage
Serviço S3-compatible local que persistência as imagens e anexos anexados no Outline. Possui os buckets `outline-holding` e `outline-br4nds` rodando localmente de forma isolada.

---

## 🤖 Regras de Conexão e Comportamento para Agentes de IA

Ao operar nesta stack na VPS, todo agente de IA deve seguir estas diretrizes sem exceção:

### 1. Arquitetura Multi-Bot no Discord
* **NUNCA tente compartilhar o mesmo Token de Bot do Discord entre agentes/containers separados.**
* Conexões simultâneas do gateway do Discord com o mesmo token geram erro de *Session Conflict* (um container derruba a conexão WebSocket do outro em loop).
* **Cada agente (Diretor, Produto, Growth, etc.) deve possuir seu próprio Bot e seu próprio token exclusivo no Discord.**

### 2. Acesso ao Teable via API (Evite Queries SQL brutas)
* Para ler, inserir ou deletar registros no Teable, utilize as ferramentas de MCP disponíveis (`teable_query`, `teable_insert`, etc.) que batem na API REST oficial em `http://factorio_teable:3000` (porta interna) ou `https://db.markeologia.com.br`.
* Evite rodar comandos SQL brutos via terminal (`psql` do container `factorio_teable_db`), exceto para manutenções administrativas de emergência. A API do Teable garante o versionamento e a integridade da UI.

### 3. Persistência de Memória Semântica
* Sempre que tomar uma decisão arquitetural, consertar um bug ou obter credenciais novas, salve esse fato no AgentMemory.
* Isso garante que os outros robôs (e futuras sessões de agentes de IA) consigam resgatar a informação sem quebrar o contexto de produção.
