import { task } from "@trigger.dev/sdk/v3";
import { getPythonPath, execFileAsync } from "../utils/pythonHelper.ts";
import * as path from "path";
import { renderVideo } from "./renderer.ts";


interface TranscribePayload {
  recordId: string;
}

export async function runTranscriber(payload: TranscribePayload) {
  const { recordId } = payload;
  console.log(`🎙️ [channelsyt_treasuresspurgeon] Iniciando Task de Transcrição via DB para: ${recordId}`);

  const scriptPath = path.resolve(__dirname, '../scripts/transcribe_db.py');
  const pythonCmd = getPythonPath();
  const args = [scriptPath, "--record-id", recordId];

  console.log(`▶ Executando: ${pythonCmd} ${args.join(" ")}`);
  const { stdout, stderr } = await execFileAsync(pythonCmd, args);
  
  console.log("Stdout:", stdout);
  if (stderr) {
    console.error("Stderr:", stderr);
  }

  // Encadeamento instantâneo (Fluxo Feliz) para a Renderização de Vídeo
  try {
    const dbHelperPath = path.resolve(__dirname, '../scripts/render_db.py');
    const { stdout: infoStdout } = await execFileAsync(pythonCmd, [dbHelperPath, "--record-id", recordId, "--get-info"]);
    const info = JSON.parse(infoStdout.trim());
    const { transcriptPath } = info;

    const createNextScript = path.resolve(__dirname, '../scripts/create_next_task.py');
    const { stdout: nextStdout } = await execFileAsync(pythonCmd, [
      createNextScript,
      "--parent-id", recordId,
      "--next-task", "render-video",
      "--area", "channels",
      "--instruction", transcriptPath
    ]);
    console.log(`[PIPELINE] Próxima task enfileirada: ${nextStdout.trim()}`);

    const cleanId = recordId.replace("task_transcribe_", "");
    const nextTaskId = `task_render_${cleanId}`;
    
    console.log(`🚀 [channelsyt_treasuresspurgeon] Encadeamento de renderização PAUSADO. Apenas registrando a task no banco para ${nextTaskId}...`);
    // await renderVideo.trigger({ recordId: nextTaskId });
  } catch (e: any) {
    console.warn(`⚠️ [channelsyt_treasuresspurgeon] Não foi possível encadear renderização automaticamente: ${e.message || e}`);
  }
  
  return { status: "success", info: stdout };
}

export const transcribeAudio = task({
  id: "mananciall/channels/yt_en_treasures_spurgeon/transcribe-audio",
  maxDuration: 1200, // 20 minutos
  queue: {
    name: "channelsyt_treasuresspurgeon-transcribe-queue",
    concurrencyLimit: 1, // Um transcritor por vez
  },
  run: runTranscriber,
});
