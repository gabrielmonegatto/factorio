# 🗂️ CÂNONE DO NOTION — os bancos do Business System

> Escrito em 03/09/2026 (sessão de arquitetura com o Gabriel). Este doc é a FONTE do
> desenho; o Notion é a vitrine. O mapa que a MÁQUINA lê é `tools/notion/canone.json`.
> Construtor idempotente: `node tools/notion/notion-canone.mjs [--aplicar]`.

## §1 A decisão

O Business System volta a ser um sistema, e não uma pilha de bancos. Antes: **98 bancos**
no workspace, com papéis disputados dentro do próprio Business System (dois "Tasks", dois
inventários de automação, dois catálogos de métrica). Agora: **16 bancos canônicos**, todos
costurados por `Unidade` e `Área`, e um mapa declarado que diz o que é da fábrica.

**A correção que gerou a regra (03/09):** o que vive fora do Business System (Life System,
Dojo, Br4nds, Catálogo de Métricas) NÃO é entulho, é outro espaço com finalidade própria.
Máquina não mexe em espaço alheio. Por isso o cânone existe como arquivo: sem ele, a busca
da API devolve tudo e a máquina trata o pessoal do Gabriel como se fosse território dela.

## §2 O filtro (o que vira banco no Notion)

Três perguntas. Não pras três, não é banco daqui:

1. O Gabriel precisa VER e DECIDIR sobre isso?
2. A linha é MACRO? (uma obra, um canal, uma oferta, uma tarefa; nunca um capítulo, um
   evento de funil, uma sessão de visita)
3. O volume cabe numa tela? (dezenas ou centenas, não dezenas de milhares)

**Banco grande entra como ESPELHO DE AGREGADO, nunca como lista.** A linha é a fonte, com
contadores escritos pela máquina, e um link que abre o `bi.mananciall.org` já filtrado.
Vale pra Fontes (as milhares de obras ficam no D1), Canais (os vídeos ficam no D1),
Ofertas (pedidos ficam no D1), Referências (os 36 mil vídeos de concorrente ficam no D1).

## §3 Os 16 bancos

### Bloco 1: chão da fábrica (governança)

| Banco | 1 linha = | Papel |
|---|---|---|
| `Unidades` | um negócio | Mananciall, Bluue, ZOAC, Entelekkia. Costura tudo |
| `Áreas` | uma área | as 7 áreas + Growth, com estado de ativação |
| `Tasks` | uma tarefa macro | **A FILA ÚNICA.** Contrato de máquina: `Gate` (auto/aprovação), `Prompt`, `Exec` |
| `Roadmap` | uma entrega | marcos por área e onda (W0/W1/W2) |
| `Esteiras` | uma automação | o que roda sozinho: cadência, gatilho, código, saúde |

### Bloco 2: o manual (o que guia os agentes)

| Banco | 1 linha = | Papel |
|---|---|---|
| `POPs` | um procedimento | vitrine do catálogo de skills do git. **O git é a fonte** |
| `Recursos` | uma ferramenta | pra que serve, custo, e ONDE vive a credencial (senha nunca) |

### Bloco 3: os ativos (o que a fábrica produz e vende)

| Banco | 1 linha = | Papel |
|---|---|---|
| `Biblioteca Mananciall` | uma obra | catálogo editorial (202 obras) |
| `Artigos Enciclopédia` | um verbete | a enciclopédia |
| `Bíblia Mananciall · Revisão` | um capítulo | revisão das edições Clássica e Simples (1.189 linhas). Entrou em 10/09, ver §9 |
| `Canais` | um canal | canais próprios por marca e plataforma |
| `Conteúdos` | uma peça | publicados em qualquer formato (longo, short, post, artigo) |
| `Ofertas` | uma oferta | o que é vendável: preço, página, gateway |

### Bloco 4: mercado e aprendizado

| Banco | 1 linha = | Papel |
|---|---|---|
| `Fontes` | uma fonte | mineração: legalidade, robots, contadores, link pro BI |
| `Referências` | uma referência | curadoria de terceiros que serve de modelo |
| `Experimentos` | um teste | hipótese, resultado, aprendizado |
| `Indicadores` | uma métrica | valor atual espelhado do D1, com meta |

## §4 O que foi feito em 03/09 (tudo não destrutivo)

**Criados:** `Fontes`, `Conteúdos`, `POPs`, `Recursos`, `Canais` (sob a página Factorio) e
`Ofertas` (sob a página Ecommerce). Esqueleto mínimo de propósito: coluna se ganha no uso.

**Fusões (rename preserva o id, então script que aponta pro banco continua vivo):**

| Antes | Agora | Por quê |
|---|---|---|
| `Workflows` | **`Esteiras`** | era o inventário alimentado pela máquina (doc 18 → D1 → Notion) e o mais rico (gatilho, onde roda, log) |
| `Esteiras` (v1, ago/26) | `[APOSENTADO] Esteiras v1` | inventário manual, criado por mim em 19/08, com papel duplicado. Nada apagado |
| `Referências de Editoras` | **`Referências`** | as 609 linhas de editoras continuam; o banco passa a caber criativo, página e canal |

**Adotados com a costura da casa** (ganharam `Unidade`/`Área`): `Experimentos`, `Indicadores`.

**Semeados:** POPs com as 5 skills da fábrica; Fontes com STEM, CCEL e o acervo Banzoli.

## §5 As duas descobertas da lixeira

| Banco | Situação | Decisão |
|---|---|---|
| `Unidades` | estava na **lixeira** do Notion | **RESTAURADO.** É o eixo: Tasks, Experimentos, Metas e Projetos todos apontam pra ele, e toda relação nova falhava por causa disso |
| `Backlog de Canais` | criado e descartado em 02/09 | **NÃO ressuscitado.** Banco no lixo é decisão do Gabriel. `Canais` nasceu limpo herdando a taxonomia de arquétipo dele (Treasures, Bíblia, Best Of, Vault, Histórias, Autoridade). Importar as linhas antigas depende de ordem dele |

## §6 Fusão que foi CANCELADA (e por quê)

`Métricas` → `Indicadores`: **não fizemos.** A simulação mostrou 40 linhas que são do
Br4nds/Bluue (MER, ROAS Meta, CPM, fadiga de criativo), morando na página `Catálogo de
Métricas`. É o catálogo de OUTRO espaço, não duplicata do Indicadores da fábrica. O banco
fica intocado; a função de migração segue no script como referência.

> A lição que vale mais que a fusão: **rodar em simulação antes de aplicar.** Foi o dry run
> que impediu de poluir o Indicadores da fábrica com 40 métricas de tráfego pago de cliente.

## §7 Gotchas do Notion aprendidos nesta rodada

| Mina | Onde morde |
|---|---|
| **Banco na lixeira responde GET e falha em PATCH** | `Could not find database with ID` mesmo com a leitura funcionando. Antes de investigar permissão, checar se está no lixo (o `fetch` do MCP mostra o atributo `deleted`) |
| **Relação exige o DATA SOURCE vivo, não só o banco** | criar relação pra banco na lixeira falha com `Could not find data_source with ID`, citando um id que você nunca escreveu (o da data source, diferente do id do banco) |
| **Banco novo do Notion não aceita o endpoint antigo** | bancos criados no modelo novo (multi data source) recusam `PATCH /v1/databases` da versão 2022-06-28. Usar a conexão MCP nova pra eles |
| **Rename preserva o id** | é o que torna fusão barata: renomear não quebra script nenhum que já aponte pro banco |
| **A busca da API devolve o workspace inteiro** | inclusive espaço pessoal. Por isso o cânone é arquivo declarado, não descoberta por busca |

## §8 Pendências

- Fundir `Esteira Editorial` na `Biblioteca Mananciall` (mesmo grão: a obra). Alto risco de
  atrapalhar o cockpit editorial do Gabriel: fazer COM ele, não por conta.
- Idem `Roadmap Editorial` → `Roadmap` + `Tasks`.
- Ligar os contadores: esteira que preenche `Fontes` (obras/mineradas/na fila), `Canais`
  (publicados/inscritos) e `Ofertas` (vendas 7d) a partir do D1.
- Views (board, filtro) são manuais na UI: a API não cria view.

## §9 Entradas depois de 03/09

### `Bíblia Mananciall · Revisão` (10/09/2026)

- **Id:** `3d7f06f1-0ce3-8179-a470-c76c89429cf2`, sob a página Business System (mesmo pai da
  Biblioteca). Chave no `canone.json`: `bibliaRevisao`.
- **Grão:** um capítulo. 1.189 linhas. É exceção consciente ao filtro do §2 ("nunca um
  capítulo"): aqui o capítulo É a unidade de decisão humana (o Gabriel aprova ou pede ajuste
  capítulo a capítulo), o volume é fixo e não cresce, e a revisão não tem outra casa com tela.
- **Fonte:** D1 `mananciall-db-dev` (só leitura), pelo script versionado
  `apps/eternall/mananciallbible/scripts/notion_revisao.mjs`. Idempotente, chave de upsert é a
  coluna `Chave` (`Jo-3`).
- **Donos das colunas:**

| Coluna | Dono | Regra |
|---|---|---|
| Capítulo, Chave, Livro, Testamento, Ordem, Versículos, Escrita, Bancada | máquina | reescritas a cada rodada se o D1 mudar |
| Revisão Fable | máquina | `Revisar` na criação; depois só muda com fonte da máquina (`--fable`) |
| Revisão humana | **Gabriel** | a máquina põe `Revisar` na criação e nunca mais toca |
| Nota | **Gabriel** | a máquina nunca escreve |
