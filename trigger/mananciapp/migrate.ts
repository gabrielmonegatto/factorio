import { task } from "@trigger.dev/sdk/v3";
import { getPythonPath, execFileAsync } from "../utils/pythonHelper.ts";
import * as path from "path";

export async function runAudiobookMigration() {
  console.log("🚀 [Trigger.dev] Iniciando task de migração de audiobooks para R2...");

  const scriptPath = path.resolve(__dirname, '../scripts/migrate_local_to_r2.py');
  const cmd = getPythonPath();
  const args = [scriptPath];

  console.log(`▶ Executando: ${cmd} ${args.join(" ")}`);
  
  // Executa o script python de migração. O timeout é longo pois são 1.120 devocionais.
  const { stdout, stderr } = await execFileAsync(cmd, args, { maxBuffer: 1024 * 1024 * 10 }); // 10MB buffer
  
  console.log("Stdout:", stdout);
  if (stderr) {
    console.error("Stderr:", stderr);
  }

  return { status: "success", info: stdout };
}

export const migrateAudiobooks = task({
  id: "mananciall/produto/audiobooks/migrate",
  maxDuration: 1800, // 30 minutos (tempo mais do que seguro para converter e enviar 1.120 arquivos)
  queue: {
    name: "mananciall-migration-queue",
    concurrencyLimit: 1, // Apenas uma migração por vez
  },
  run: runAudiobookMigration,
});
