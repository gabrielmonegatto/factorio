# 🤖 AGENT.md — Onboarding para Agentes de IA (EternalL Holding)

Seja bem-vindo, agente de IA. Este é o seu manual de instruções para entender a operação, a arquitetura e a stack da **EternalL Holding** antes de começar a codificar ou interagir.

---

## 🧭 Regras Gerais e Filosofia
1. **Regra de Ouro (user_global):** "Não minta, não tenha vergonha de falar a real, Deus abençoe." Seja transparente sobre bugs, limitações e problemas. Não tente esconder se cometer erros, pois faz parte do processo, nem fantasie resultados ou dados que você não tem certeza.
2. **Pragmatismo:** Menos teoria, mais código executável e verificação prática.
3. **Validação:** Sempre verifique se o que você fez funciona (rode os scripts locais, teste o banco, confira logs do Trigger.dev).

---

## 🏭 A Operação (Factorio)
A nossa operação autônoma é chamada de **Factorio** (localizada em `_factorio/`). Basicamente estamos construindo uma fábrica de negócios automatizada, atualmente com os seguintes pilares:

inteligência - dados do mercado estruturados para modelagem de funis, produtos, conteúdos, etc.
mineração - pesquisa e extração de matéria prima para criação de conteúdos, produtos, vetores, etc.
produto - área de produtos.
channels - área de conteúdos em diversos formatos.
growth - área de crescimento: funis de aquisição, monetização, retenção, etc.
software - área de desenvolvimento de software.
i18n - internacionalização de toda a operação.
P&D - pesquisa e desenvolvimento de tudo que possa elevar o nível da operação.


tarefas de processamento de conteúdo (livros teológicos, devocionais, etc.), sintetiza áudio (Text-To-Speech) e gerencia filas de tarefas.

---

## 🛠️ Stack Tecnológica

| Componente                              | Tecnologia                  | Detalhes                                                             |
| --------------------------------------- | --------------------------- | -------------------------------------------------------------------- |
| **Orquestração**                        | **Trigger.dev v3/v4**       | Localmente iniciado via `npm run dev` (`npx trigger.dev@latest dev`) |
| **Banco de Dados**                      | **Postgres (Teable local)** | `postgresql://teable:teable_secret_password@localhost:42345/teable`  |
| **Interface de Dados**                  | **Teable**                  | Permite ao usuário visualizar tabelas como planilhas                 |
| **Chaves de API** `.env` do `_factorio` |

---

Qualquer dúvida pergunte antes de queimar tokens pesquisando coisas triviais. tamo junto! Deus abençoe!

