# 🧬 UNIFICAÇÃO DE DADOS — aposentadoria do Teable e do trigger.dev

> Executado em 19/08/2026, na mesma sessão que desenhou o `16_BLUEPRINT_AREAS.md`.
> Pergunta que abriu a frente (do Gabriel): *"nosso Teable hoje não seria uma peça a mais avulsa?
> isso não poderia morar num banco no D1 e a visualização a gente criar no BI?"*
> Resposta curta: sim. Este doc é o registro do porquê, do como, e do que ficou de fora.

---

## 1. O diagnóstico

O Teable tinha dois papéis no desenho de julho: **estado tabular da máquina** e **grid humano com views**.
Os dois foram tomados por outras peças, na prática, sem ninguém decidir:

- Estado da máquina → **D1**. Toda esteira construída desde julho nasceu lá (mineração, edição, A/B da Bluue, tracking, BI do Br4nds). Nenhuma nasceu no Teable.
- Grid humano → **Notion** (curadoria) e **BI** (leitura de número).

Sobrou um Postgres self-hosted pra cuidar, com dívida acumulada:

| Sintoma | Detalhe |
|---|---|
| Cert TLS vencido | `db.markeologia.com.br`: curl passa, Python urllib recusa |
| Tabela `tasks` quebrada na API | 400 Invalid FieldId desde julho (campos criados via SQL bruto com IDs manuais). Ninguém sentiu falta em 1 mês |
| Paginação travando | Tabelas de conteúdo bíblico congeladas em 1.001 linhas |
| Views corrompidas | `mcp` e `agent_journal` devolvem 400; `content_chunks` devolve 500 |

**Padrão que se repete:** serviço self-hosted que duplica papel de algo gerenciado vira dívida. Foi assim com o Outline (morto em 23/07) e foi assim aqui.

**trigger.dev caiu junto, pelo mesmo teste:** nada em produção usava. Render é `systemd`, agendador é `cron`, esteiras são script idempotente com fila no D1 (`works`/`runs`), que já entrega o retry e a observabilidade que o orquestrador venderia. Se um dia precisar de orquestração gerenciada de verdade, o caminho é Cloudflare Workflows/Queues, mesma casa do D1.

## 2. A regra que ficou

```
Cadência simples ................. cron na VPS + health check no #fabrica
Pipeline multi-etapa ............. script idempotente + fila no D1 (padrão mineração)
Volume/estado .................... D1        Binário .......... R2
Curadoria humana ................. Notion    Código ........... git
```

## 3. O que foi executado

### 3.1 Export completo (a garantia de que nada se perde)

`scripts/migracao/teable_export.mjs` → **119.356 linhas** de todas as bases (Eternall, Br4nds, Zoac), uma NDJSON.gz por tabela + `MANIFESTO.json` com esquema de campos. Arquivo no R2: `eternall-archives/teable/2026-08-19/`.

Três tabelas não exportaram (defeito antigo do próprio Teable, não da migração). Diagnosticadas uma a uma, **sem perda real de dado** (§3.4).

### 3.2 O que virou D1

Banco novo **`eternall-intel`** (`d2e1bda6-9202-4b27-a1ef-a590e689b80a`), que era o ouro abandonado desde abril:

| Tabela | Linhas | O que é |
|---|---|---|
| `channels` | 50 | Canais concorrentes com inscritos/views/vídeos/língua |
| `channel_videos` | 36.739 | Vídeos com views, likes, engajamento, tier, categoria: raio-X do que performa no nicho |
| `players` | 17 | Concorrentes das 3 marcas (Eternall, Br4nds, Zoac) |
| `player_creatives` | 1.421 | Anúncios com copy, headline, dias no ar, oferta, gancho |
| `player_pages` | 293 | Páginas raspadas com copy, estrutura de funil, checkout |
| `authors` | 422 | Índice de autores |
| `research` | 518 | Pesquisa acumulada |
| `sources` | 21 | Fontes |
| `wiki_articles_staging` | 8 | Verbetes golden (a frente Content move pro `mananciall-db` na F1 da wiki) |

E `content_index` (545 obras, a fonte que a mineração consulta pra resolver URL) foi pro banco **`mananciall-mining`**, junto da fila que já vive lá.

**Desenho das tabelas:** colunas úteis tipadas (as que a gente consulta) + coluna `raw` com o JSON original inteiro. Preserva 100% do dado sem gastar dias modelando, e dá pra promover campo do `raw` pra coluna quando surgir necessidade.

### 3.3 O que virou só arquivo (R2, sem D1)

Matéria-prima morta que não precisa de banco vivo: 655 artigos do Hermes + 319 do pipeline (formulaicos, sem fonte: são matéria-prima, não produto), as tabelas `bible_*` (69.195 linhas do `biblehub_index` são URLs `pending`: a miragem aposentada pelo ADR 004 do app de Bíblia), `br4nds_criativos` (3.448: o índice dos criativos que já vivem no R2), e os restos da era Hermes (`agents`, `org_chart`, `cycles`, `skills`, `tools`).

### 3.4 As três tabelas que não exportaram (diagnóstico)

| Tabela | Erro | O que é de verdade |
|---|---|---|
| `content_chunks` | 500 | `relation "bseWeczeNfCSaMlu2EC.tblFyPPXJTiynzBKFH2" does not exist`: **registro fantasma**. O Teable lista a tabela nos metadados, mas a tabela física não existe no Postgres. Não há dado a perder |
| `mcp` | 400 Invalid FieldId | Mesmo defeito da `tasks`: campo criado via SQL bruto com ID manual. Metadados quebrados, era Hermes |
| `agent_journal` | 400 Invalid TableId | ID manual `tblAgentJournal001` não é ID válido do Teable. `row-count` diz 5 linhas de diário de agente da era Hermes |

**Nenhuma perda.** E as três reforçam a decisão: as avarias vêm todas de schema criado por fora da API oficial, num serviço que ninguém mantinha.

## 4. O que NÃO mudou (de propósito)

- **A camada de gestão continua no Notion** até o BI absorver (fim de 2026). Ela é curadoria semanal, não volume.
- **Bases de cliente (Br4nds/Zoac)**: os dados foram exportados e migrados pro `eternall-intel` como intel, mas qualquer mudança de fluxo operacional da Br4nds é decisão da frente dela.
- **A VPS continua viva**: ela perde o papel de banco, não o de músculo (render, TTS, rebuild do BI, cron).

## 5. Minas aprendidas nesta rodada

| Mina | Onde morde |
|---|---|
| **U+2028/U+2029 quebram NDJSON** | São JSON válido e `JSON.stringify` não os escapa, mas o `readline` do Node trata como quebra de linha → "Unterminated string in JSON". Apareceu em descrição de vídeo do YouTube. Fix: escapar na escrita e quebrar só em `\n` na leitura |
| **D1 aceita ~100 parâmetros vinculados por query** | Migrar 36 mil linhas com `?` viraria 7 mil requests. Fix: gerar SQL literal escapado e mandar em arquivo pelo `wrangler d1 execute --file`, fatiado em ~3,5 MB |
| **Caractere de controle quebra o parser do wrangler** | Ao gerar SQL literal, remover `\x00-\x1f` além de dobrar aspa simples |
| **Schema criado fora da API oficial quebra a ferramenta** | A `tasks` do Teable morreu assim (IDs de campo manuais via SQL bruto). Vale pra qualquer ferramenta com API: não escrever no banco dela por baixo |
| **Credencial em doc commitado** | O `STACK.md` carregava o token do Teable e a chave do AgentMemory em texto plano. Removidos na reescrita; o histórico do git ainda guarda: rotacionar ao desligar |

## 6. Pendências desta frente

- [ ] **Gabriel:** revogar o token do Teable e a chave `factorio_secret` quando os containers forem desligados (estão no histórico do git).
- [ ] **Gabriel:** corrigir a linha malformada no `.env` (`PADDLE_WEBHOOK_SECRET:` com dois-pontos em vez de `=`), senão nenhum leitor de `.env` acha a variável.
- [ ] Congelar containers do Teable na VPS (`docker stop` + `restart=no`, sem apagar volume) e observar 7 dias antes de remover.
- [ ] Frente Content: mover `wiki_articles_staging` pro `mananciall-db` na F1 da wiki.
- [ ] Frente Int. de Mercado: a W0 deixou de ser "mapear do zero" e virou **resgatar e atualizar** o que já está no `eternall-intel` (última mineração: abril/2026). Os gaps reais são players EN e o segmento de apps.
