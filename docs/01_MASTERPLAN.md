# 🎯 MASTERPLAN — A FÁBRICA DE NEGÓCIOS ETERNALL

> Escrito em 18/07/2026, na sessão de redesenho com Claude (Fable 5 / Claude Max).
> Este documento é a VISÃO e o RACIONAL. O "como operar" está no `02_OPERATING_MODEL.md`.

---

## 1. O que é a Fábrica

A Fábrica (Factorio) é o sistema que **constrói e opera negócios digitais em série**: canais de conteúdo, funis D2C, sites com produtos e áreas de membros. Ela não é um prédio de robôs ligados 24/7 — é um **ciclo**:

```
Conhecimento em arquivos versionados
        ↓
Trabalho de julgamento feito por sessões de Claude seguindo SOPs (skills)
        ↓
Trabalho repetitivo feito por esteiras determinísticas (trigger.dev)
        ↓
Tudo auditado (git), registrado (Teable/Outline) e medido
        ↓
Aprendizado volta pros arquivos → o ciclo melhora
```

**A unidade de produção da fábrica é o TEMPLATE**: um negócio que foi construído uma vez, manualmente e com qualidade, e depois congelado como esteira + skill reproduzível. Meta de maturidade: acionar `/novo-canal`, `/nova-marca`, `/novo-site` e receber a unidade pronta em horas/dias, não semanas.

## 2. A tese (por que redesenhamos agora)

A fábrica 1.0 foi desenhada para **compensar modelos fracos**: agentes Python com LLM barato, memória semântica própria (AgentMemory), diretor-robô (Hermes), multi-bot Discord, MCP universal caseiro. Muito encanamento para pouco cérebro. As cicatrizes: `autoCure.ts`, configs corrompidos, handoffs com erros, stash quase-desastre.

Com o Claude Max, a equação inverte: **inteligência deixou de ser o gargalo**. O gargalo agora é *contexto de qualidade, verificação e disciplina de processo*. Prova empírica interna: o que mais produziu resultado nos últimos meses foi wiki versionada + sessões de Claude com regras claras (`apps/br4nds/_wiki/`), não a frota de agentes.

**Logo: dobramos a aposta no que venceu.** O desenho 2.0 tem menos peças, cada uma no seu ponto forte.

## 3. Os 3 planos

| Plano | Peças | Papel |
|---|---|---|
| **Conhecimento** | Outline (narrativa) + Git (código/SOPs) | O que a fábrica sabe e como ela age |
| **Dados** | Teable (operacional) + D1 (produto) + R2/MinIO (assets) | O que a fábrica registra e mede |
| **Execução** | Claude Code (QG) + trigger.dev (esteiras) + LLM-função + CF Workers/Pages + RunPods (GPU) | Quem faz o quê |

## 4. Decisões tomadas e racional

| # | Decisão | Racional resumido |
|---|---|---|
| D1 | **Claude Code é o QG** (central de operações) — permanece pra sempre | É onde vive o julgamento: construir, decidir, revisar, consertar. Harness maduro (skills, subagents, MCP, memória) + melhor modelo. Custo fixo via Max. |
| D2 | **trigger.dev é a central de workflows** — permanece | Retry, cron, filas e observabilidade prontos. Claude escreve as tasks; elas rodam pra sempre. |
| D3 | **LLM-como-função para volume** | Passos repetitivos com "um pouco de cérebro" (limpar, traduzir, titular) = chamada de API com prompt fixo dentro da task. Barato e escalável. Agente ≠ função. |
| D4 | **Aposentar a camada de agentes** (Hermes, agentes Python, AgentMemory, mcp_universal, bots Discord) | Papel de julgamento migra pras sessões; código determinístico bom é destilado em scripts; memória migra pra Outline/Teable/git. Detalhe peça por peça no `05_LEGACY_TRANSITION.md`. |
| D5 | **Outline = o "Notion" da holding** (camada narrativa) | Interface única HUMANA. Não é banco único físico — é casa única por natureza de dado (racional completo no `03_DATA_ARCHITECTURE.md`). |
| D6 | **Fábrica opera por cadência, não 24/7** | Sessões agendadas (diária/semanal/sob demanda). Casa com limites do Max, com guard-rails e com qualidade (verificação > loop contínuo). |
| D7 | **Notificação = 1 webhook** (sem bots de gateway) | Gateway multi-bot existia por causa da frota. A fábrica avisa; a conversa acontece no Claude Code. Bridge conversacional Discord = projeto futuro opcional (Agent SDK). |
| D8 | **Stack de linguagens não muda** | TypeScript (esteiras/Workers) + Astro (sites) + Python só onde já ganha o pão (scripts destilados). A revolução é o modelo operacional, não a linguagem. |

## 5. O que permanece da filosofia 1.0 (intocável)

- **As 3 camadas de dados**: CONTENT → INDEX → TASKS. O dado É o estado.
- **As 8 áreas** (Inteligência, Mineração, Produto, Channels, Growth, Software, i18n, P&D) como taxonomia de departamentos.
- **Desacoplamento radical**: áreas e esteiras isoladas, interdependência só via estado no banco.
- **Runner burro, decisão em quem pensa**: esteira não decide; julgamento não processa volume.
- **Anti-padrões** (1 task por chunk, status redundante, filas intermediárias) continuam proibidos.

O que muda é o **substrato**: quem decidia (Hermes/agentes) vira sessão de Claude com skill; quem executava volume (workers Python em loop) vira task trigger.dev.

## 6. Papéis humanos e limites

- **Gabriel (CEO)**: agora — constrói o sistema junto (sessões de construção intensivas). Depois — direciona e aprova em 1–2h/dia.
- **Gates humanos obrigatórios** até a skill ganhar confiança: gastar dinheiro, publicar externamente, mexer em campanha/budget, deletar dados. (Níveis de confiança no `02_OPERATING_MODEL.md`.)
- **Realismo**: a fábrica entrega *produção* em velocidade. Retenção de audiência, monetização e risco de moderação das plataformas são problemas de negócio que template nenhum elimina — por isso todo template novo passa por piloto com gate de qualidade humano antes de escalar.

## 7. Fronteiras desta frente

A operação de tracking/campanhas da Bluue (purchase-check, LF 8) é **outra frente**, tocada em sessões próprias com fonte de verdade em `apps/br4nds/_wiki/Holding/`. A fábrica não mexe lá; quando os departamentos por cadência entrarem (Fase 4 do roadmap), a interface entre fábrica e Br4nds será definida explicitamente.
