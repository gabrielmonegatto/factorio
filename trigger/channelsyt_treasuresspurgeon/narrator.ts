import { task } from "@trigger.dev/sdk/v3";
import { getPythonPath, execFileAsync } from "../utils/pythonHelper";
import * as path from "path";
import { transcribeAudio } from "./transcriber";

interface NarratePayload {
  recordId: string; // ID da tarefa no Teable
}

export async function runNarrator(payload: NarratePayload) {
  const { recordId } = payload;
  console.log(`🎙️ [channelsyt_treasuresspurgeon] Iniciando Task de Narração via DB para: ${recordId}`);

  const scriptPath = path.resolve(__dirname, '../scripts/narrator_db.py');
  const cmd = getPythonPath();
  const args = [scriptPath, "--record-id", recordId];

  console.log(`▶ Executando: ${cmd} ${args.join(" ")}`);
  const { stdout, stderr } = await execFileAsync(cmd, args);
  
  console.log("Stdout:", stdout);
  if (stderr) {
    console.error("Stderr:", stderr);
  }
  
  // Encadeamento instantâneo (Fluxo Feliz)
  const cleanId = recordId.replace("task_spurgeon_", "");
  const nextTaskId = `task_transcribe_${cleanId}`;
  
  try {
    console.log(`🚀 [channelsyt_treasuresspurgeon] Encadeamento instantâneo: disparando transcribeAudio para ${nextTaskId}...`);
    await transcribeAudio.trigger({ recordId: nextTaskId });
  } catch (e: any) {
    console.warn(`⚠️ [channelsyt_treasuresspurgeon] Não foi possível encadear transcrição automaticamente: ${e.message || e}`);
  }

  return { status: "success", info: stdout };
}

export const narrateAudio = task({
  id: "mananciall/channels/yt_en_treasures_spurgeon/narrate-audio",
  maxDuration: 1200, // 20 minutos
  queue: {
    name: "channelsyt_treasuresspurgeon-narrate-queue",
    concurrencyLimit: 1, // 🚀 Executa estritamente um narrador por vez
  },
  run: runNarrator,
});
