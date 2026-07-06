# 🏭 Trigger.dev Automations — EternalL Holding

Este diretório contém as automações do sistema **Factorio** orquestradas via **Trigger.dev v3**.

## 🧭 Padrão de Nomenclatura Único

Para manter o repositório escalável e organizado, todas as tarefas registradas no Trigger.dev e no banco de dados devem utilizar o padrão de identificador único de **4 níveis**:

```
brand/area/project/task
```

### Exemplos Práticos:
- **Canais (Youtube/Redes):** `mananciall/channels/yt_en_treasures_spurgeon/narrate-audio`
- **Produtos/Livros:** `mananciall/produto/books/publish`
- **Produtos/Audiobooks:** `mananciall/produto/audiobooks/migrate`
- **Software/Infraestrutura:** `mananciall/software/factorio/universal-cron`

> [!NOTE]
> Mesmo que algumas tarefas possam parecer completas com 3 níveis, **utilize sempre 4 níveis** para manter a consistência e compatibilidade com o parser de rotas e banco de dados.

---

## 📁 Diretório de Saídas (`zoutputs`)

Todas as automações e scripts que geram arquivos físicos (áudios, transcrições, vídeos, etc.) devem salvar os arquivos no seguinte caminho padrão:

```
_factorio/zoutputs/<brand>/<project>/
```

### Exemplo:
Os áudios gerados pelo narrador do Spurgeon são gravados em:
`_factorio/zoutputs/mananciall/yt_en_treasures_spurgeon/`

> [!TIP]
> A pasta chama-se `zoutputs` com "z" para que fique sempre por último na listagem de pastas do repositório, facilitando a navegação visual.

---

## ⏱️ Consolidação de Crons (Universal Cron)

O plano gratuito do Trigger.dev tem um limite de **10 crons agendados**. Para evitar estourar a cota:
1. **Não declare novos crons independentes** com `schedules.task` diretamente nos arquivos de pipelines.
2. Centralize a lógica no [universalCron.ts](file:///c:/Users/Monegatto/Desktop/EternalL/_factorio/trigger/utils/universalCron.ts).
3. O `universal-cron` roda a cada 15 minutos e executa:
   - Auto-cura (`auto_cure_tasks.py`) para liberar tarefas travadas.
   - Sincronização de pipelines (`enqueue_pipeline_tasks.py`) para puxar novos dados para o banco.
   - Busca por tarefas pendentes (`get_pending_tasks.py`) e disparo das mesmas via `.trigger()` nativo usando a tabela de switch-case centralizada.

### Como adicionar uma nova automação periódica:
1. Crie seu arquivo de `task` normalmente no respectivo diretório de domínio (ex.: `mananciapp/` ou `channels/`).
2. Adicione o mapeamento do ID canônico no `switch-case` de `universalCron.ts` e chame `seuJob.trigger({ ... })`.
3. Caso precise exportar para compatibilidade, re-exporte o `universalCron` a partir do seu arquivo de cron legado:
   ```ts
   import { universalCron } from "../utils/universalCron";
   export const cronLegado = universalCron;
   ```
