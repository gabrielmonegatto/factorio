# Teable Schemas — EternalL Factory (Jul 2026)

## Connection

```bash
docker exec factorio_teable_db psql -U teable -d teable
```

Port 42345 (mapped to host).

## Schemas

| Schema | Tables | Rows | Purpose |
|--------|--------|------|---------|
| `bseWeczeNfCSaMlu2EC` | 58 | ~69k | **Base principal** — TASKS, content, YouTube data |
| `bseyIWRa5nyTWMlNBpi` | 21 | ~1.6k | Base secundária |
| `bseX6gpT5qn1T4Iq7Ph` | 5 | ~15 | Base terciária |
| `public` | 3 | 0 | Internal Teable metadata (task, task_run, task_reference) — always empty |

## Key Tables (Schema `bseWeczeNfCSaMlu2EC`)

### TASKS — `tblVzN1Eo8tfk7GX2CJ` (425 records)

| Column | Type | Description |
|--------|------|-------------|
| `__id` | text | Primary key |
| `Task_ID` | text | Human-readable task name |
| `Status` | text | Pendente / Concluído / Em Processamento |
| `task` | text | Task type slug |
| `area` | text | channels / produto |
| `progresso` | text | "N/M" format |
| `brand` | text | mananciall |
| `project_slug` | text | Project identifier |
| `__created_time` | timestamptz | Creation timestamp |

**Task types:** `translate-content` (85), `publish-books-en` (85), `transcribe-audio` (85), `narrate-audio-en` (85), `narrate-audio` (85)

**Status breakdown (425 total):** Pendente (365), Concluído (36), Em Processamento (24)

### YouTube Data — `tblz2WQnbhh06TEa7Ro` (36,739 records)

YouTube video metadata: youtube_id, title, description, publish_date, view_count, like_count, channel_name, mining_status.

### Bible Verses — `tbl9cM460hpuqi2jbqv` (69,195 records)

Verse references: url, section, book, chapter, verse, author, status.

### Agent Journal — `tblAgentJournal001` (5 records)

Diretor observations: agent, type (observation/alert), summary, context.

### Content Index — `tblD7Kxoc7gFTgEWoWo` (545 records)

**This is the `content_index` table** — the catalog of all discovered content.

| Column | Type | Description |
|--------|------|-------------|
| `Name` | text | Human-readable work name |
| `title` | text | Full title |
| `author` | text | Author name (may include multiline) |
| `brand` | text | Business unit (e.g. 'mananciall') |
| `font_id` | text | Source font ID |
| `source_url` | text | Original source URL |
| `pipeline_state` | jsonb | Aggregated pipeline status (metadata, mineracao, i18n, produto) |
| `project_slug` | text | Project identifier |

**Current state (Jul 2026):**
- 91 items with `brand = 'mananciall'` (all in "minerado" state)
- Authors: Spurgeon (78), Bounds (6), Edwards (5), Enoch (1)
- `pipeline_state` currently only has `metadata` and `historical_category` — the i18n/produto nodes are populated via TASKS table, not yet synced back to INDEX

**Key query — Mananciall catalog:**
```sql
SELECT "Name", title, author, pipeline_state
FROM "bseWeczeNfCSaMlu2EC"."tblD7Kxoc7gFTgEWoWo"
WHERE brand = 'mananciall'
ORDER BY author;
```

### Factory Knowledge — `tblFactoryKnowledge` (0 records)

Schema exists but empty: title, category, tags, content, source, confidence.

## Query Examples

```bash
# All schemas
docker exec factorio_teable_db psql -U teable -d teable -c \
  "SELECT schema_name FROM information_schema.schemata \
   WHERE schema_name NOT IN ('information_schema','pg_catalog','pg_toast','public') \
   ORDER BY schema_name;"

# Row estimates for all tables in a schema
docker exec factorio_teable_db psql -U teable -d teable -c \
  "SELECT table_name, \
     (SELECT reltuples::bigint FROM pg_class \
      WHERE oid = (quote_ident(table_schema) || '.' || quote_ident(table_name))::regclass) \
     AS row_estimate \
   FROM information_schema.tables \
   WHERE table_schema='bseWeczeNfCSaMlu2EC' \
   ORDER BY row_estimate DESC NULLS LAST;"

# Task status breakdown
docker exec factorio_teable_db psql -U teable -d teable -c \
  "SELECT \"Status\", count(*) AS total \
   FROM \"bseWeczeNfCSaMlu2EC\".\"tblVzN1Eo8tfk7GX2CJ\" \
   GROUP BY \"Status\" ORDER BY total DESC;"

# Latest tasks
docker exec factorio_teable_db psql -U teable -d teable -c \
  "SELECT \"Task_ID\", \"Status\", task, area, \"progresso\" \
   FROM \"bseWeczeNfCSaMlu2EC\".\"tblVzN1Eo8tfk7GX2CJ\" \
   ORDER BY \"__created_time\" DESC LIMIT 10;"
```

## Pitfalls

- **`pg_stat_user_tables` returns empty** — stats collector is off in the container. Use `reltuples` from `pg_class` instead.
- **Column names with capital letters** — must be double-quoted: `"Status"`, `"Task_ID"`
- **Table names are UUIDs** — always double-quoted: `"tblVzN1Eo8tfk7GX2CJ"`
- **Schema names change if Teable is recreated** — the `bse*` prefix is base-specific. Run the schema discovery query first to find current names.