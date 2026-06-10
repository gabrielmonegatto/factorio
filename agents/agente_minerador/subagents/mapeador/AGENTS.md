# AGENTS.md - Subagente Mapeador

## Missão

> Receber a URL raiz de uma fonte (ex.: `https://www.stempublishing.com/`) e **mapear** toda a hierarquia de livros/artigos disponíveis. O agente deve:

1. Navegar pelas páginas da fonte.
2. Extrair títulos, autores, URLs de download (PDF/HTML) e metadados relevantes.
3. Normalizar os campos (remover espaços, unificar capitalização).
4. Inserir os registros nas tabelas Baserow `authors_index` e `content_index` usando a API.
5. Emitir um relatório resumido de quantos itens foram criados e quais potenciais duplicatas foram encontradas.

## Como o Líder delega

- O **Agente Líder** lê a taskflow `Mapear Fonte: Stem Publishing` (status `Iniciar!`).
- Ao reconhecer a palavra‑chave **"Mapear"**, ele cria uma instância do subagente `mapper_subagent` passando a URL da fonte como `input_url`.
- O subagente executa o fluxo abaixo e devolve `{"status": "ok", "report": {...}}`.
- O Líder então chama a **validação QA** (`validate_mapping_qa.py`). Se a QA passar, o Líder marca a taskflow como `Concluída!`; caso contrário, envia um alerta para o CEO.

## Ferramentas Necessárias (skills)

- `read_file` – para ler arquivos auxiliares (ex.: lista de stop‑words).
- `write_file` – para gerar logs temporários.
- `run_command` – opcional para instalar dependências (`pip install -r requirements.txt`).
- **Bibliotecas Python** (listadas em `requirements.txt`):
  - `requests`
  - `beautifulsoup4`
  - `python-dotenv`
  - `fuzzywuzzy` (ou `thefuzz`)

## Estrutura de Arquivos do Subagente

```
subagents/
  mapeador/
    AGENTS.md                # ← este arquivo
    workers/
      spider_worker.py      # crawling da fonte
      baserow_insert.py     # inserção de registros no Baserow
    validation/
      validate_mapping_qa.py  # deduplicação e QA
```

## Fluxo de Execução (pseudo‑código)

```python
from workers.spider_worker import crawl_source
from workers.baserow_insert import upsert_content, upsert_author
from validation.validate_mapping_qa import run_qa

async def main(input_url: str):
    # 1️⃣ Crawl
    items = crawl_source(input_url)
    # 2️⃣ Upsert autores e conteúdos
    for item in items:
        author_id = upsert_author(item["author"], item["author_url"])
        upsert_content(
            title=item["title"],
            url=item["url"],
            author_id=author_id,
            source="Stem Publishing"
        )
    # 3️⃣ QA
    report = run_qa(source="Stem Publishing")
    return {"status": "ok", "report": report}
```

---

**Nota:** O subagente **não** altera a taskflow. Ele apenas devolve o relatório; a responsabilidade de mudar o status está no Agente Líder (conforme descrito acima).
