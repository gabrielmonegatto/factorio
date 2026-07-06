---
name: knowledge-consolidation
description: "Find scattered docs about a domain, map their evolution/tensions, and unify into a single folder with a consolidating README."
version: 2.2.0
author: Diretor de Operações
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [documentation, consolidation, archaeology, knowledge-management, refactoring]
    related_skills: [codebase-inspection, plan]
---

# knowledge-consolidation

Find scattered documentation about a domain/concept across a project tree, read everything, map the evolution, identify tensions, and produce a unified README.

## Triggers

Load this skill when the user says things like:
- "pesquisa ai na raiz, em brain, e na pasta X sobre os arquivos de Y"
- "unifica todos esses arquivos numa pasta"
- "me tira todas as duvidas e consolida esse aprendizado"
- "find all docs about X and unify them"
- "consolidate everything we know about Y"
- "map out the documentation for feature Z"

## Steps

### 1. Discover — find every file

Search across **all likely directories** (root, `_brain/`, `docs/`, `scratch/`, `archive/`) with multiple patterns:

```
search_files(path=".", pattern="*topic*", target="files")
search_files(path="_brain", pattern="*topic*", target="files")
search_files(path="_brain", pattern="*synonym*", target="files")
```

Key patterns to try:
- Exact term: `*factorio*`, `*fabrica*`
- Synonyms: `*factory*`
- Shorthand: `*fct*`

If a path doesn't exist (e.g. `brain/` vs `_brain/`), `search_files` returns a "Similar paths" hint — use it.

### 2. Dig deeper — check for nested folders

The first pass may find index files. Check for deeper folder structures:

```
search_files(path="_brain/projectz/_topic", pattern="*", target="files")
```

Read every `.md` file found. Batch independent reads together.

### 3. Read the originals — don't skip

Read every file. If results are truncated (50+ files), use `offset` to paginate. Prioritize:
- ⭐ starred files (they're marked as important by the user)
- `README.md` (often the index)
- Files with the primary topic in their name

### 4. Map the evolution

Organize findings chronologically or by conceptual maturity:
- **Phase 1** — raw ideas, lists, early notes
- **Phase 2** — structure emerges (setores, architecture)
- **Phase 3** — paradigm shift (new model/approach)
- **Phase 4** — current state / philosophy

For each phase, note:
- What document represents it
- Key ideas introduced
- Tensions with other phases

### 5. PRESENT & CONFIRM — CRITICAL! Do NOT skip

**This is the most important step.** Do NOT proceed to unification until the user has confirmed.

Present your findings to the user as:
1. **How many files found and where** — "Encontrei N documentos espalhados em X locais"
2. **The evolution timeline** — phases identified
3. **Tensions and open questions** — format as 3-5 specific numbered questions about contradictions, unclear stack, missing info
4. **Ask explicitly** if the user wants to proceed with unification, or if they want you to explore further first

**Why this matters:** Consolidating too early creates work that needs to be redone when the user fills in context you didn't know you were missing. The user may have a richer mental model than any single document captures.

**Iterative cadence:** The user will likely say "vai me perguntando" or "não consolide nada ainda" multiple times. Each time, ask ONE focused question at a time — don't dump 5 questions in one message. Let each answer guide the next question. The user's corrections (e.g. "não são 6 áreas, são 8", "o banco é Teable, ponto") are the real payload — they're filling in the gap between docs and reality. Only when the user says "faz a faxina" or "consolida" do you proceed to unification.

### 6. Unify into a single folder (only after user confirmation)

**First: decide WHERE.** Ask yourself: does the user already have an organized folder for this domain (e.g. `_brain/projectz/_factorio/`)? If yes, work INSIDE it — don't create a parallel folder at root. Only create a new root folder if no existing home exists.

**Then: TRIAGE AND CLEAN UP.** Not every file belongs in the final folder. Classify each file:

| Class | Action |
|-------|--------|
| **Core domain doc** | Keep in the main folder |
| **Third-party reference** | Move to `tools_ref/` or `ref/` subfolder |
| **Stale / deprecated** | Move to `_archive/` (don't delete — history matters) |
| **Off-topic / not from this project** | Move to `_archive/` |

Create the archive and ref folders:
```bash
mkdir -p _archive tools_ref
```

Move classified files. The central manual you'll write should reference the `_archive/` folder so users know where the old docs went.

**Then: consolidate the core docs.** Copy (or work in-place if using the existing folder) with clean names:
- Replace spaces with underscores
- Remove emoji prefixes (⭐ → remove)
- Rename ambiguously-named files (e.g. `factorio.md` → `agent_paradigm_teable.md`)
- Keep the original name when it's already descriptive

### 7. Write the consolidating README (or CENTRAL MANUAL)

The goal is a document that future agents read FIRST to understand the domain. Two directions:

- **Simple README** (index + evolution + tensions) — good for small domains with few documents and no live system
- **Central Manual** (⭐ prefix, e.g. `⭐ MANUAL_DA_FABRICA.md`) — better for complex domains with a running system (factory, pipeline, SSOT database). This replaces the README entirely and serves as THE authoritative reference. Other docs remain as supporting detail.

The README must contain:

1. **Directory structure** — a clean tree of what's now in the folder
2. **Evolution timeline** — phases with document-to-phase mapping
3. **Tensions and open questions** — contradictions between documents, decision points, unresolved ambiguities (format these as numbered questions for the user)
4. **Next steps suggestion** — what could be done after the user answers the questions

### 8. Save the result to memory

Write a compact memory entry covering:
- How many files were unified
- Where they live now
- The evolution phases identified
- Key tensions/decisions pending

## Pitfalls

- **Truncated results:** `search_files` limits to 50 results. Use `offset` for pagination or narrow with `file_glob`.
- **Missing context:** Files in `_brain/` often reference other files in the same folder. Check `docs/README.md` files — they're often the index.
- **Rename without trace:** When creating a NEW consolidated folder (at project root), always COPY. The originals may be referenced by other docs. When CLEANING UP the user's existing folder (e.g. archiving junk to `_archive/`), MOVING is correct — the junk leaves the main view.
- **Don't create parallel folders:** The user may already have an organized folder (e.g. `_brain/projectz/_factorio/`). Check before creating a new root-level folder. Ask: "tem uma pasta organizada pra isso?" Work within their structure. Parallel folders confuse future agents and split the source of truth.
- **One-file-one-name:** Don't merge documents into a single file unless they're duplicates. Keep the original granularity.
- **Stale memory references:** The user's memory may reference a file that no longer exists or has moved. Verify the actual file path.
- **❌ Consolidating too early:** This is the #1 mistake. Present findings as questions first. The user has context you don't. "Vai me perguntando" means stop and ask — do not unify until the user says go.
- **📌 User corrections are the real payload:** When the user corrects a structural detail (e.g. "não são 6 áreas, são 8", "o banco é Teable, ponto"), that IS the answer to your open question. Integrate it immediately into your mental model. Don't ask "mas o doc X diz Y" — the user's word overrides the docs.
- **📌 Ask where to consolidate BEFORE creating folders:** The user may have an existing folder for this domain. Ask "tem uma pasta organizada pra isso?" or look for `_brain/projectz/_topic_name/`. If they say "considere e consolide os arquivos na pasta que organizei pra vc: path/to/folder", COPY files into their folder — do NOT create a parallel folder at root.
- **Dump no more than 1-2 questions per turn:** 5 questions at once overwhelms the user. Ask one or two, get the answer, then the next. The user said "eai ta dificil ein" when hit with 5 questions — that's a signal to pace yourself.
- **Not checking the database:** When the domain involves a running system (business OS, factory, pipeline), the docs are historical but the database is the live state. Check both. Treat docs as "what was planned" and the database as "what is."

## Extended reconnaissance: checking the live system

When a project involves a live database (not just docs), add this step after Step 3:

### 3b. Check the live database

Look for:
- A running Postgres/Supabase/Teable instance — check `.env` files, `docker ps`, and existing scout scripts
- Connection strings in `.env` at `_factorio/.env`, `apps/*/.env.local`, or agent dirs
- Existing Python scripts in `scratch/` that probe the database (name patterns: `*inspect*`, `*check*`, `*list*`, `*scout*`, `*teable*`, `*baserow*`)
- For **Teable** specifically:
  - REST API at `http://localhost:3000` with Bearer token auth (get token from existing scripts)
  - Endpoints: `/api/space` → `/api/space/{id}/base` → `/api/base/{id}/table` → `/api/table/{id}/field`
  - Direct Postgres at `localhost:42345` (user: `teable`, db: `teable`)
  - The token can be stored in a `.teable_token.json` file to avoid passing it in terminal commands (Hermes redacts credentials from terminal output)
- For **Baserow**: REST API at configured port with token auth

Always prioritize the REST API over direct Postgres (it's self-documenting and doesn't need password auth).

Format the live state as a tree diagram in your presentation to the user.

## Verification

After finishing, show the user:
- "✅ N files copied to topic/"
- A clean tree of the new folder
- The numbered open questions from the README
