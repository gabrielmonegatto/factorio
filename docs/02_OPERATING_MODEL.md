# ⚙️ OPERATING MODEL — COMO A FÁBRICA FUNCIONA

> Este é O documento de processo. Qualquer sessão (Claude ou humano) segue este fluxo.
> Se algo aqui conflitar com a prática, a prática vence — e este doc é atualizado na hora.

---

## 1. A taxonomia de execução (quem faz o quê)

| Camada | Ferramenta | O que faz | O que NUNCA faz |
|---|---|---|---|
| **QG (julgamento)** | Claude Code (Max) | Construir, desenhar, decidir, revisar, diagnosticar, orquestrar. Escreve e conserta todo o resto. | Produzir volume repetitivo (30 vídeos/dia não é sessão — é esteira) |
| **Esteiras (volume)** | trigger.dev (tasks TS em `_factorio/trigger/`) | Pipelines determinísticos com retry/cron/fila: minerar, traduzir, narrar, renderizar, publicar | Decidir. Esteira burra é esteira saudável |
| **LLM-função** | Chamada de API dentro de uma task (Haiku / modelo de volume via OpenRouter) | Passo repetitivo que precisa de "um pouco de cérebro": limpar HTML, traduzir chunk, titular vídeo. Prompt fixo + saída estruturada | Loop agêntico, decisão em aberto |
| **Runtime de produto** | Cloudflare Workers/Pages + D1 | Servir sites, APIs, tracking dos negócios | — |
| **GPU pesada** | RunPods (acionado pelas esteiras) | Render de vídeo em lote | Ficar ligada sem fila |
| **Agente embutido** (futuro) | Claude Agent SDK | Agente vivendo dentro de um produto (chat de atendimento, respondedor de webhook) | Ser usado onde uma sessão ou uma função resolve |

**Regra de escolha de cérebro:** decisão em aberto → sessão Claude · passo repetitivo com prompt fixo → LLM-função · sem ambiguidade nenhuma → código puro sem LLM.

**A regra de ouro que amarra tudo:**

```
Claude Code CONSTRÓI a esteira → a esteira PRODUZ o volume → Claude Code
SUPERVISIONA por cadência e MELHORA o template. Repete.
```

## 2. O Ciclo Padrão (toda unidade de trabalho passa por aqui)

```
1. PEDIDO      → nasce do Gabriel (sessão interativa) ou de rotina agendada
2. REGISTRO    → se é operação de fábrica: task no Teable (TASKS), 1 task = 1 operação
3. CONTEXTO    → a sessão carrega a skill (SOP) + lê estado (Teable) + narrativa (Outline)
4. EXECUÇÃO    → sessão faz o julgamento; subagents pra paralelismo; esteira pra volume
5. VERIFICAÇÃO → checklist de pronto DA PRÓPRIA SKILL (ver §5) — nada é "pronto" sem verificar de verdade
6. REGISTRO    → código → git (commit) · narrativa → Outline · estado → Teable
7. NOTIFICAÇÃO → resumo curto no webhook (#fabrica)
8. APRENDIZADO → o que se aprendeu vira atualização da skill/doc — NUNCA fica só na conversa
```

O passo 8 é o mais importante da fábrica inteira: **a fábrica aprende em arquivos, não em memória oculta.** Sessão que descobre algo e não atualiza a skill desperdiçou a descoberta.

## 3. Tipos de sessão

| Tipo | Quem inicia | Exemplo | Cadência |
|---|---|---|---|
| **Construção** | Gabriel | "Vamos montar o template de canal dark" | Sob demanda (fase atual: intensiva) |
| **Rotina** | Agendamento | `/diretor-diario`, `/intel-semanal` | Fixa (diária/semanal) — começa manual, automatiza quando a skill amadurece |
| **Operação pontual** | Gabriel ou rotina | "Diagnostica por que a esteira X travou" | Sob demanda |

## 4. Coordenação multi-sessão (várias frentes em paralelo)

Gabriel roda várias sessões ao mesmo tempo. Pra não virar bagunça:

1. **1 sessão = 1 frente = 1 escopo de arquivos.** Sessão da fábrica não edita `apps/br4nds/bluue/`; sessão da Bluue não edita `_factorio/`.
2. **O quadro compartilhado é a TASKS no Teable.** Sessão que assume uma operação marca in-progress; que termina, marca done. Qualquer sessão consegue ver o que as outras frentes estão fazendo com 1 consulta.
3. **Handoff entre frentes** = doc no Outline + task no Teable. Nunca "combinado verbal" dentro de uma conversa (a outra sessão não vê).
4. **Conflito de escopo?** Para, pergunta pro Gabriel, documenta a fronteira nova aqui.

## 5. Skills = SOPs executáveis (o catálogo da fábrica)

- Skill vive em **git** (`.claude/skills/` do repo). O Outline tem só a página-catálogo (lista + descrição de 1 linha), nunca uma cópia do conteúdo.
- Toda skill define obrigatoriamente: **(a)** gatilho e inputs, **(b)** passo a passo, **(c)** checklist de pronto (DoD) com verificação real, **(d)** nível de confiança atual.
- **Níveis de confiança** (promoção exige 3 execuções limpas consecutivas):

| Nível | O que significa |
|---|---|
| 🟡 **Draft** | Em construção/teste. Só roda em sessão de construção com Gabriel junto |
| 🟠 **Supervisionada** | Roda em rotina, mas TODA ação de dinheiro/publicação externa pede aprovação antes |
| 🟢 **Confiável** | Roda em rotina com autonomia no seu escopo. Ações destrutivas continuam SEMPRE com gate humano |

- **Gates humanos permanentes** (nenhuma skill fica isenta): gastar dinheiro · mexer em campanha/budget · publicar em plataforma externa · deletar dados · credenciais.

## 6. O Meta-SOP: como se constrói um template de negócio

Todo template (canal dark, funil D2C, site+membros...) nasce pelo MESMO processo de 6 etapas. É proibido pular etapa — velocidade vem de repetir o processo, não de atropelá-lo.

| Etapa | O que acontece | Output obrigatório |
|---|---|---|
| **1. Idealização** | Objetivo, referência de mercado, KPI de sucesso, riscos | Doc no Outline (1 página) |
| **2. Design** | Desenho da esteira: etapas, dados (3 camadas), ferramentas, custos | Doc no Outline + schema no Teable |
| **3. Implementação** | Código das tasks + LLM-funções + skill draft | Código em git, esteira deployada |
| **4. Piloto** | Rodar **1 unidade real ponta a ponta** com verificação manual de cada etapa | Unidade publicada + relatório do piloto |
| **5. Refinamento** | Ajustar até **3 unidades saírem limpas** sem intervenção | Changelog no doc de design |
| **6. Templatização** | Congelar: skill `/novo-X` promovida, template documentado | Skill 🟠 + página no catálogo |

> Este processo é o mesmo que Gabriel já usava ("processo macro → design → implementa e testa → refina") — agora oficializado para TODOS os templates.

## 7. Filosofia de dados das esteiras (herdada da 1.0 — continua lei)

- **CONTENT** (granular): o dado É o estado. Output existe = etapa feita. Sem campo `status` redundante no JSONB.
- **INDEX** (agregado): 1 row por projeto; JSONB `pipeline` com contadores. Consultar 1 row = saber tudo do projeto.
- **TASKS** (dashboard): 1 task = 1 operação de alto nível. NUNCA 1 task por chunk.
- Fluxo do runner: pega pendente na CONTENT → processa → salva output → incrementa INDEX → reflete na TASKS. Sem fila intermediária.
- Reconciliação periódica reconta CONTENT → corrige INDEX (proteção contra crash).
- Anti-padrões completos e histórico: `legacy/07_GLOSSARIO.md` (continua válido como referência).

## 8. As 8 áreas (taxonomia de departamentos)

Inteligência · Mineração · Produto · Channels · Growth · Software · i18n · P&D.
Cada área terá suas skills e esteiras; a TASKS no Teable dá a visão transversal. Rotinas por área entram na Fase 4 do roadmap.

## 9. Cadências (alvo quando a fábrica estiver operacional)

| Rotina | Cadência | Skill | Output |
|---|---|---|---|
| Diretor diário | 1x/dia (manhã) | `/diretor-diario` | Briefing no Outline + webhook (10 linhas) |
| Intel semanal | 1x/semana | `/intel-semanal` | Relatório de concorrentes/tendências no Outline |
| Revisão de esteiras | 1x/semana | `/revisao-esteiras` | Saúde das esteiras, custos, gargalos |
| Construção | Sob demanda | (várias) | Templates novos, melhorias |
