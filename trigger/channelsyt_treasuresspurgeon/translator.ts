import { task } from "@trigger.dev/sdk/v3";
import { getPythonPath, execFileAsync } from "../utils/pythonHelper.ts";
import * as path from "path";
import * as fs from "fs";

interface TranslatePayload {
  projectIndexId?: string;
  chunkId?: string;
  limit?: number;
}


export async function runTranslator(payload: TranslatePayload) {
  const { projectIndexId, chunkId, limit = 10 } = payload;
  console.log(`🌐 [channelsyt_treasuresspurgeon] Iniciando Task de Tradução/Revisão para: Project=${projectIndexId}, Chunk=${chunkId}`);

  const scriptPath = path.resolve(__dirname, '../scripts/translate_revision_db.py');
  const cmd = getPythonPath();
  
  const args: string[] = [scriptPath];
  if (projectIndexId) {
    args.push("--project-id", projectIndexId);
    args.push("--limit", limit.toString());
  } else if (chunkId) {
    args.push("--chunk-id", chunkId);
  } else {
    throw new Error("Deves fornecer projectIndexId ou chunkId no payload.");
  }

  console.log(`▶ Executando: ${cmd} ${args.join(" ")}`);
  const { stdout, stderr } = await execFileAsync(cmd, args);
  
  console.log("Stdout:", stdout);
  if (stderr) {
    console.error("Stderr:", stderr);
  }

  return { status: "success", info: stdout };
}

export const translateContent = task({
  id: "mananciall/produto/books/translate-content",
  maxDuration: 300, // 5 minutos
  queue: {
    concurrencyLimit: 1,
  },
  run: runTranslator,
});
