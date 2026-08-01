#!/usr/bin/env bash
# aplicar_role_fabrica.sh — cria/atualiza o role `fabrica` (leitura + update, sem DDL).
#
# Roda na VPS:  bash aplicar_role_fabrica.sh <SENHA>
# Idempotente: pode rodar de novo sem estragar nada.
set -euo pipefail

SENHA="${1:?uso: aplicar_role_fabrica.sh <SENHA>}"
CT=factorio_teable_db

psql() { docker exec -i "$CT" psql -U teable -d teable -v ON_ERROR_STOP=1 "$@"; }

echo "▶ criando/atualizando role fabrica..."
psql -q <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fabrica') THEN
    CREATE ROLE fabrica LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
  END IF;
END \$\$;
ALTER ROLE fabrica WITH PASSWORD '${SENHA}';
GRANT CONNECT ON DATABASE teable TO fabrica;
SQL

echo "▶ liberando SELECT+UPDATE (e SÓ isso) nos schemas do Teable..."
for SCH in $(docker exec "$CT" psql -U teable -d teable -t -A -c \
      "SELECT nspname FROM pg_namespace WHERE nspname LIKE 'bse%'"); do
  psql -q <<SQL
GRANT USAGE ON SCHEMA "${SCH}" TO fabrica;
GRANT SELECT, UPDATE ON ALL TABLES IN SCHEMA "${SCH}" TO fabrica;
REVOKE INSERT, DELETE, TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA "${SCH}" FROM fabrica;
REVOKE CREATE ON SCHEMA "${SCH}" FROM fabrica;
-- tabelas criadas no futuro herdam a mesma regra
ALTER DEFAULT PRIVILEGES IN SCHEMA "${SCH}" GRANT SELECT, UPDATE ON TABLES TO fabrica;
SQL
  echo "   ✓ ${SCH}"
done

echo "▶ schema proprio da fabrica (poder total la dentro)..."
psql -q <<SQL
CREATE SCHEMA IF NOT EXISTS factory AUTHORIZATION fabrica;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
SQL

echo "✅ role fabrica pronto."
