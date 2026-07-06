# Como Acessar o Banco Postgres do Teable Local Diretamente

O Teable local é executado em containers Docker e armazena seus dados em um banco de dados PostgreSQL. Por ser um sistema NoCode baseado em banco de dados, você pode ler e alterar os dados diretamente via SQL, o que elimina a dependência de tokens de API REST e resolve problemas de autenticação (`401 Unauthorized`).

---

## 🔑 Credenciais do Postgres Local
* **Host:** `localhost`
* **Porta física (exposta):** `42345`
* **Banco de dados (DB):** `teable`
* **Usuário:** `teable`
* **Senha:** `teable_secret_password`
* **URL de Conexão:** `postgresql://teable:teable_secret_password@localhost:42345/teable`

---

## 🧱 A Estrutura de Schemas (Isolamento de Bases)
O Teable isola cada **Base** (Workspace/Projeto) em um schema PostgreSQL separado. O nome do schema é o **ID da Base** no Teable.

### Principais Bases e Schemas Identificados:
1. **Base Factorio (SSOT de Projetos e Tarefas):**
   * **ID da Base (Schema):** `bseWeczeNfCSaMlu2EC`
   * **Tabela de Tarefas (tasks):** `"bseWeczeNfCSaMlu2EC"."tblVzN1Eo8tfk7GX2CJ"`
   * **Tabela de Projetos (projects):** `"bseWeczeNfCSaMlu2EC"."tblalvN0Db5K9S7Hrb6"`

2. **Base Mananciall (Pipeline de Sermões):**
   * **ID da Base (Schema):** `bseWeczeNfCSaMlu2EC`
   * **Tabela de Conteúdos (content_index):** `"bseWeczeNfCSaMlu2EC"."tblD7Kxoc7gFTgEWoWo"`

---

## 🛠️ Como Mapear e Executar Queries via Python

Para rodar queries nas tabelas físicas do Teable, você deve **sempre qualificar a tabela com o nome do schema**. Exemplo em Python (`psycopg2`):

```python
import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgresql://teable:teable_secret_password@localhost:42345/teable"
SCHEMA = "bseWeczeNfCSaMlu2EC"
TASKS_TABLE = f'"{SCHEMA}"."tblVzN1Eo8tfk7GX2CJ"'

def obter_task(record_id):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # IMPORTANTE: Sempre use aspas duplas no nome qualificado por causa de letras maiúsculas/minúsculas no Postgres
    cur.execute(f'SELECT * FROM {TASKS_TABLE} WHERE __id = %s', (record_id,))
    task = cur.fetchone()
    
    conn.close()
    return task
```

---

## ⚡ Regras de Colunas Internas do Teable
Ao manipular registros diretamente pelo Postgres, preste atenção aos seguintes metadados exigidos pelas tabelas do Teable:
* `__id`: String única que representa o ID do registro no Teable (ex: `recSpurgeonTaskTest`).
* `__version`: Inteiro de controle de versão (sempre envie `1` no insert inicial).
* `__created_time`: Timestamp do momento de criação (use `NOW()`).
* `__created_by`: ID do usuário que criou o registro (campo **NOT NULL**). Use o ID padrão `'usrCe4LHiMshx2Cw3C0'` (do usuário gabriel.monegatto).
