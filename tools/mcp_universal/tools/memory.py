import json
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "memory.db"

TIERS = {
    "working": "observacoes brutas, efemero, limpo a cada sessao",
    "episodica": "resumos de sessoes completadas",
    "semantica": "fatos, conceitos, padroes extraidos",
    "procedural": "workflows, decisoes arquiteturais, scripts",
}

def _get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tier TEXT NOT NULL DEFAULT 'working',
            conceito TEXT NOT NULL,
            conteudo TEXT NOT NULL,
            tags TEXT DEFAULT '',
            confianca REAL DEFAULT 1.0,
            fonte TEXT DEFAULT '',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            ultimo_acesso REAL,
            acesso_count INTEGER DEFAULT 0
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_tier ON memory(tier)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_conceito ON memory(conceito)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_confianca ON memory(confianca)")
    conn.commit()
    return conn

def register_tools(mcp):

    @mcp.tool()
    async def memory_save(tier: str, conceito: str, conteudo: str, tags: str = "", confianca: float = 1.0, fonte: str = "") -> str:
        now = time.time()
        conn = _get_db()
        conn.execute(
            "INSERT INTO memory (tier, conceito, conteudo, tags, confianca, fonte, created_at, updated_at, ultimo_acesso) VALUES (?,?,?,?,?,?,?,?,?)",
            (tier, conceito, conteudo, tags, confianca, fonte, now, now, now),
        )
        conn.commit()
        conn.close()
        return f"Memoria '{conceito}' salva em tier '{tier}'."

    @mcp.tool()
    async def memory_search(consulta: str, tier: str = "", limite: int = 10) -> list:
        conn = _get_db()
        like = f"%{consulta}%"
        if tier:
            rows = conn.execute(
                "SELECT id, tier, conceito, conteudo, tags, confianca, ultimo_acesso, acesso_count FROM memory WHERE (conceito LIKE ? OR conteudo LIKE ? OR tags LIKE ?) AND tier = ? ORDER BY confianca DESC LIMIT ?",
                (like, like, like, tier, limite),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, tier, conceito, conteudo, tags, confianca, ultimo_acesso, acesso_count FROM memory WHERE conceito LIKE ? OR conteudo LIKE ? OR tags LIKE ? ORDER BY confianca DESC LIMIT ?",
                (like, like, like, limite),
            ).fetchall()

        results = [dict(r) for r in rows]
        for r in results:
            conn.execute("UPDATE memory SET acesso_count = acesso_count + 1, ultimo_acesso = ? WHERE id = ?", (time.time(), r["id"]))
        conn.commit()
        conn.close()
        return results

    @mcp.tool()
    async def memory_update(conceito: str, conteudo: str = None, confianca: float = None, tags: str = None) -> str:
        conn = _get_db()
        campos = []
        valores = []
        if conteudo is not None:
            campos.append("conteudo = ?")
            valores.append(conteudo)
        if confianca is not None:
            campos.append("confianca = ?")
            valores.append(confianca)
        if tags is not None:
            campos.append("tags = ?")
            valores.append(tags)
        if not campos:
            conn.close()
            return "Nada a atualizar."
        campos.append("updated_at = ?")
        valores.append(time.time())
        valores.append(conceito)
        conn.execute(f"UPDATE memory SET {', '.join(campos)} WHERE conceito = ?", valores)
        conn.commit()
        conn.close()
        return f"Memoria '{conceito}' atualizada."

    @mcp.tool()
    async def memory_promover(conceito: str, tier_destino: str) -> str:
        conn = _get_db()
        row = conn.execute("SELECT * FROM memory WHERE conceito = ?", (conceito,)).fetchone()
        if not row:
            conn.close()
            return f"Memoria '{conceito}' nao encontrada."
        conn.execute("UPDATE memory SET tier = ?, updated_at = ? WHERE id = ?", (tier_destino, time.time(), row["id"]))
        conn.commit()
        conn.close()
        return f"Memoria '{conceito}' promovida para tier '{tier_destino}'."

    @mcp.tool()
    async def memory_consolidar(tier_origem: str = "working") -> int:
        conn = _get_db()
        rows = conn.execute("SELECT * FROM memory WHERE tier = ? ORDER BY updated_at ASC", (tier_origem,)).fetchall()
        conn.close()
        return len(rows)

    @mcp.tool()
    async def memory_status() -> dict:
        conn = _get_db()
        tiers = {}
        for row in conn.execute("SELECT tier, COUNT(*) as qtd FROM memory GROUP BY tier").fetchall():
            tiers[row["tier"]] = row["qtd"]
        conn.close()
        return {
            "total": sum(tiers.values()),
            "por_tier": tiers,
            "tiers_descricao": TIERS,
        }

    return mcp
