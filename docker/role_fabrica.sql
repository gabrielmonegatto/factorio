-- role_fabrica.sql — blindagem do Teable contra humano E contra IA.
--
-- PROBLEMA: existe um único role no Postgres (`teable`, SUPERUSER) e é ele que está
-- no `.env`. Qualquer agente com o `.env` pode DROPAR tabela do Teable. Foi exatamente
-- assim que nasceram os fantasmas `mcp` e `content_chunks`, as colunas invisíveis
-- (`pipeline_state`) e os 425 registros com `__id` inventado que a API não consegue escrever.
--
-- SOLUÇÃO: um role `fabrica` que pode LER e ATUALIZAR VALOR, mas NÃO pode mudar estrutura.
-- Não é disciplina ("não faça"), é permissão ("não consegue").
--
-- Matriz de permissão nos schemas do Teable (bse*):
--   SELECT  ✅  relatório rápido, não corrompe nada
--   UPDATE  ✅  corrigir valor de célula (ex: backfill de `lang`) — não mexe em metadata
--   INSERT  ❌  era assim que nasciam registros com __id fora do padrão (API não escreve neles)
--   DELETE  ❌  perda de dado
--   CREATE/DROP/ALTER ❌  era assim que nasciam fantasma e coluna invisível
--
-- Criar/apagar tabela e coluna passa a ser SÓ pela API do Teable, que mantém a metadata
-- em dia. E a fábrica ganha o schema `factory`, onde manda em tudo.

-- 1) o role da fábrica (a senha é injetada pelo script que chama este arquivo)
--    NOSUPERUSER NOCREATEDB NOCREATEROLE: não escala privilégio.

-- 2) leitura + atualização de valor nos schemas do Teable, e nada além disso.
--    (roda para cada schema bse*; ver aplicar_role_fabrica.sh)

-- 3) schema próprio da fábrica, onde ela tem poder total.
CREATE SCHEMA IF NOT EXISTS factory AUTHORIZATION fabrica;

-- 4) trava explícita: sem CREATE nos schemas do Teable nem no public.
--    (o padrão do Postgres já nega CREATE a quem não é dono, mas deixamos explícito
--     para que a intenção fique legível para quem ler depois.)
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE teable FROM PUBLIC;
GRANT CONNECT ON DATABASE teable TO fabrica;
