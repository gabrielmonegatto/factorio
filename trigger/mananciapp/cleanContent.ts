import { task } from "@trigger.dev/sdk/v3";
import { getPythonPath, execFileAsync } from "../utils/pythonHelper";
import * as path from "path";
import { Client } from "pg";

const DB_URL = process.env.DATABASE_URL || "postgresql://teable:teable_secret_password@localhost:42345/teable";
const SCHEMA = "bseWeczeNfCSaMlu2EC";
const TBL_CONTENT = `"${SCHEMA}"."tblFyPPXJTiynzBKFH2"`;

interface CleanPayload {
  limit?: number;
  dryRun?: boolean;
  importDb?: boolean;
}

export const cleanContentTask = task({
  id: "mananciall/produto/books/clean-content",
  maxDuration: 1800, // 30 minutos
  queue: {
    name: "mananciapp-clean-queue",
    concurrencyLimit: 1,
  },
  run: async (payload: CleanPayload = {}) => {
    const limit = payload.limit ?? 50; // Lote padrão seguro de 50 chunks
    const dryRun = payload.dryRun ?? false;
    const importDb = payload.importDb ?? true;

    const scriptPath = path.resolve(__dirname, '../scripts/clean_content_groq.py');
    const pythonCmd = getPythonPath();

    const args = [scriptPath, "--limit", limit.toString()];
    if (dryRun) args.push("--dry-run");
    if (importDb && !dryRun) args.push("--import-db");

    console.log(`🤖 Executando script de limpeza de chunks com python: ${pythonCmd} ${args.join(' ')}`);

    const { stdout, stderr } = await execFileAsync(pythonCmd, args);
    if (stderr && stderr.trim().length > 0) {
      console.warn(`⚠️ Logs de depuração/aviso no stderr:\n${stderr}`);
    }
    console.log(`✅ Output do script de limpeza:\n${stdout}`);
    
    const executionResult = {
      status: "success",
      output: stdout
    };

    // ── Encadeamento recursivo de tarefas (Trigger recursivo) ──────────────────
    if (!dryRun) {
      const db = new Client({ connectionString: DB_URL });
      await db.connect();
      try {
        const checkQuery = `
          SELECT COUNT(*) as pending 
          FROM ${TBL_CONTENT} 
          WHERE raw_content IS NOT NULL 
            AND raw_content != '' 
            AND (content IS NULL OR content = '')
        `;
        const { rows } = await db.query(checkQuery);
        const pendingCount = Number(rows[0]?.pending ?? 0);
        console.log(`📝 Chunks pendentes restantes no banco: ${pendingCount}`);

        if (pendingCount > 0) {
          console.log(`🔄 Encadeando próximo lote de limpeza de 50 chunks (restantes: ${pendingCount})...`);
          await cleanContentTask.trigger({ limit, dryRun, importDb });
        } else {
          console.log("🎉 Esteira de limpeza concluída com sucesso! Nenhum chunk pendente.");
        }
      } catch (e: any) {
        console.error("⚠️ Erro ao checar pendências para encadeamento:", e.message || e);
      } finally {
        await db.end();
      }
    }

    return {
      status: "success",
      limit,
      dryRun,
      importDb,
      output: executionResult.output
    };
  }
});
