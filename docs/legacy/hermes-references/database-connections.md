# Database Connections — Factory PostgreSQL Access

`psql` is NOT installed on the VPS host. All database access must go through
`docker exec` into the respective container.

## Connection Map

| Database | Container | Host Port | User | Database Name | Status |
|----------|-----------|-----------|------|---------------|--------|
| **Teable** | `factorio_teable_db` | 42345 | `teable` | `teable` | ✅ Active |
| **Outline** | `outline_db` | 54322 | `outline` | `outline` | ✅ Active |
| **Postgres Geral** | ❌ *destroyed* | ~~5432~~ | ~~postgres~~ | ~~eternall~~ | ❌ DESTROYED by Antigravity Jul 2026 — do NOT recreate |

## Password Discovery

Each container's `POSTGRES_PASSWORD` env var contains the real password. Extract
it via:

```python
def get_db_pw(container_name):
    out, err, rc = run(f"docker exec {container_name} env | grep POSTGRES_PASSWORD")
    return out.split("=", 1)[1] if "=" in out else ""
```

## Query Pattern (Recommended)

**Do NOT use inline `psql -c` with double-quoted identifiers through SSH.**
The shell escaping through multiple layers (Python → bash → psql) will strip
quotes and break schema-qualified queries. Use the **SCP+Python pattern** instead:

```python
# 1. Write the query script locally
with open("query.py", "w") as f:
    f.write("""
import subprocess
sql = '''SELECT "Name", title FROM "bseWeczeNfCSaMlu2EC"."tblD7Kxoc7gFTgEWoWo" LIMIT 5;'''
r = subprocess.run(["docker", "exec", "factorio_teable_db", "psql", 
    "-U", "teable", "-d", "teable", "-c", sql], capture_output=True, text=True)
print(r.stdout)
""")

# 2. SCP to VPS
subprocess.run(["scp", "-i", key, "query.py", "root@VPS:/tmp/"])

# 3. Execute on VPS
subprocess.run(["ssh", "-i", key, "root@VPS", "python3 /tmp/query.py"])
```

This avoids ALL shell quoting issues — the SQL stays inside Python where
double-quoted identifiers (`"tableName"`) work natively.

### Legacy Pattern (fragile — avoid for complex queries)

```python
def psql(container, user, db, query):
    # WARNING: fails for queries with double-quoted identifiers through SSH
    cmd = f"docker exec {container} psql -U {user} -d {db} -c '{query}'"
    return run(cmd)
```

### Examples (using SCP+Python pattern)

```python
# Count Mananciall products in content_index
sql = '''SELECT COUNT(*) FROM "bseWeczeNfCSaMlu2EC"."tblD7Kxoc7gFTgEWoWo" WHERE brand = 'mananciall';'''

# Completed tasks grouped by project
sql = '''SELECT "Projeto", COUNT(*) FILTER (WHERE "Status"='Concluído') as done
FROM "bseWeczeNfCSaMlu2EC"."tblVzN1Eo8tfk7GX2CJ"
GROUP BY "Projeto" ORDER BY done DESC;'''
```

## Connection Verification Script

See `scripts/db-connect.py` for a standalone verification script.

## Pitfalls

- **`pg_stat_user_tables` may be empty** — stats collector needs activity.
  Use `pg_tables + pg_total_relation_size()` as fallback for size info.
- **Quoting is tricky in shell commands** — single quotes inside
  `-c '...'` must be escaped as `'\"'\"'`. Prefer queries without inner quotes,
  or use double-quoted identifiers.
- **`PGPASSWORD` env var doesn't work** — set it inside the container instead.
  `docker exec factorio_<db> psql ...` works because the container's env has
  `POSTGRES_PASSWORD` already configured.