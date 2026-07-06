import { task } from "@trigger.dev/sdk/v3";
import { getPythonPath, execFileAsync } from "../utils/pythonHelper";
import * as path from "path";
import * as fs from "fs";
import { generateMarketing, narrateMarketing } from "./marketing";

interface RenderPayload {
  recordId: string;
}

// Auxiliar para copiar arquivos com criação recursiva de pastas
function copyFileSync(src: string, dest: string) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
  console.log(`📁 [renderer] Copiado: ${src} -> ${dest}`);
}

async function getAudioDurationFrames(audioPath: string): Promise<number> {
  const { stdout } = await execFileAsync("ffprobe", [
    "-i", audioPath,
    "-show_entries", "format=duration",
    "-v", "quiet",
    "-of", "csv=p=0"
  ]);
  const durationSeconds = parseFloat(stdout.trim());
  if (isNaN(durationSeconds)) {
    throw new Error(`Falha ao calcular duração para: ${audioPath}`);
  }
  return Math.round(durationSeconds * 30);
}

export async function runRenderer(payload: RenderPayload) {
  const { recordId } = payload;
  console.log(`🎬 [renderer] Iniciando renderização de vídeo para: ${recordId}`);

  const dbHelperPath = path.resolve(__dirname, '../scripts/render_db.py');
  const pythonCmd = getPythonPath();
  
  // Atualiza status no banco para "Em Processamento"
  await execFileAsync(pythonCmd, [
    dbHelperPath,
    "--record-id", recordId,
    "--update-status", "Em Processamento",
    "--logs", "[RENDER] Iniciando esteira de renderização automatizada...\n"
  ]);

  try {
    const { stdout: infoStdout } = await execFileAsync(pythonCmd, [dbHelperPath, "--record-id", recordId, "--get-info"]);
    const info = JSON.parse(infoStdout.trim());
    
    const { sermonDir, sermonTitle, sermonNumber, title } = info;
    const sermonSlug = path.basename(sermonDir);

    // 2. Garante geração dos textos de marketing
    console.log("🎬 [renderer] Chamando geração de marketing...");
    const marketingMeta = await generateMarketing.triggerAndWait({ recordId }).unwrap();
    
    // 3. Garante narração dos áudios de marketing
    console.log("🎬 [renderer] Chamando narração de marketing...");
    await narrateMarketing.triggerAndWait({
      recordId,
      sermonDir,
      hookText: marketingMeta.hookText,
      outroText: marketingMeta.outroText
    }).unwrap();

    const hookWav = path.join(sermonDir, "hook.wav");
    const hookJson = path.join(sermonDir, "hook.json");
    const ctaWav = path.join(sermonDir, "cta_narration.wav");
    const ctaJson = path.join(sermonDir, "cta_narration.json");

    // 4. Garante a transcrição do Hook via AssemblyAI
    const transcriberScript = path.resolve(__dirname, '../scripts/transcribe_file.py');
    if (!fs.existsSync(hookJson)) {
      console.log("🎬 [renderer] Transcrevendo hook.wav...");
      await execFileAsync(pythonCmd, [transcriberScript, "--file", hookWav]);
    } else {
      console.log("🎬 [renderer] hook.json já existe.");
    }

    // 5. Garante a transcrição da cta_narration via AssemblyAI
    if (!fs.existsSync(ctaJson)) {
      console.log("🎬 [renderer] Transcrevendo cta_narration.wav...");
      await execFileAsync(pythonCmd, [transcriberScript, "--file", ctaWav]);
    } else {
      console.log("🎬 [renderer] cta_narration.json já existe.");
    }

    // 6. Dispara o renderizador FFmpeg
    console.log("🎬 [renderer] Disparando renderizador FFmpeg...");
    const ffmpegRendererScript = path.resolve(__dirname, '../scripts/ffmpeg_renderer.py');
    
    try {
      const { stdout: renderStdout, stderr: renderStderr } = await execFileAsync(pythonCmd, [
        ffmpegRendererScript,
        "--record-id", recordId
      ], { maxBuffer: 50 * 1024 * 1024 });
      console.log("Render stdout:");
      if (renderStderr) {
        console.error("Render stderr:", renderStderr);
      }
      return { status: "success" };
    } catch (err: any) {
      console.error("❌ ERRO NO RENDER FFMPEG:", err.message || err);
      throw err;
    }
  } catch (err: any) {
    const errorMsg = `\n❌ ERRO NO RENDER: ${err.message || err}\n`;
    console.error(errorMsg);
    
    // Salva status de erro no banco
    await execFileAsync(pythonCmd, [
      dbHelperPath,
      "--record-id", recordId,
      "--update-status", "Erro",
      "--logs", errorMsg
    ]);
    
    throw err;
  }
}

export const renderVideo = task({
  id: "mananciall/channels/yt_en_treasures_spurgeon/render-video",
  maxDuration: 1800, // 30 minutos
  queue: {
    name: "channelsyt_treasuresspurgeon-render-queue",
    concurrencyLimit: 1, // Apenas um renderizador por vez para não sobrecarregar a máquina (CPU/GPU)
  },
  run: runRenderer,
});
