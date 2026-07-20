// utils/universalCron.ts
import { schedules } from "@trigger.dev/sdk/v3";
import { execFile } from "child_process";
import { promisify } from "util";
import * as path from "path";
import * as fs from "fs";
import { publishMananciappBooks } from "../mananciapp/publishBook.ts";
import { migrateAudiobooks } from "../mananciapp/migrate.ts";
import { narrateAudio } from "../channelsyt_treasuresspurgeon/narrator.ts";
import { transcribeAudio } from "../channelsyt_treasuresspurgeon/transcriber.ts";
import { translateContent } from "../channelsyt_treasuresspurgeon/translator.ts";
import { getPythonPath, execFileAsync } from "./pythonHelper.ts";


interface PendingTask {
  id: string;
  project: string;
  area: string;
  task: string;
}

/**
 * Universal cron that processes pending tasks and dispatches the appropriate script
 * based on the canonical task ID `${brand}/${area}/${project}/${task}`.
 */
export const universalCron = schedules.task({
  id: "mananciall/software/factorio/universal-cron",
  cron: "*/15 * * * *",
  maxDuration: 600, // 10 minutos
  run: async () => {
    console.log("⏱️ [UNIVERSAL] Executando cron universal de tarefas pendentes...");

    const pythonCmd = getPythonPath();

    try {
      // 1. Rodar script de Auto-Cura para destravar possíveis tarefas presas
      console.log("⏱️ [UNIVERSAL] Iniciando auto-cura...");
      const autoCurePath = path.resolve(__dirname, '../scripts/auto_cure_tasks.py');
      const { stdout: autoCureOut } = await execFileAsync(pythonCmd, [autoCurePath]);
      console.log(`⏱️ [UNIVERSAL] Auto-Cura:\n${autoCureOut.trim()}`);
    } catch (e: any) {
      console.error("❌ [UNIVERSAL] Erro ao executar auto-cura:", e.message || e);
    }

    try {
      // 2. Sincronizar pipeline (Reconciliação)
      console.log("⏱️ [UNIVERSAL] Sincronizando pipeline (Reconciliação)...");
      const reconcilePath = path.resolve(__dirname, '../scripts/reconcile_factory.py');
      const { stdout: reconcileOut } = await execFileAsync(pythonCmd, [reconcilePath]);
      console.log(`⏱️ [UNIVERSAL] Reconciliação:\n${reconcileOut.trim()}`);
    } catch (e: any) {
      console.error("❌ [UNIVERSAL] Erro ao reconciliar pipeline:", e.message || e);
    }

    // 3. Buscar tarefas pendentes no banco
    let pendingTasks: PendingTask[] = [];
    try {
      const getPendingPath = path.resolve(__dirname, '../scripts/get_pending_tasks.py');
      const { stdout } = await execFileAsync(pythonCmd, [getPendingPath]);
      pendingTasks = JSON.parse(stdout.trim()) as PendingTask[];
      console.log(`⏱️ [UNIVERSAL] Encontradas ${pendingTasks.length} tarefas pendentes no total.`);
    } catch (e: any) {
      console.error("❌ [UNIVERSAL] Erro ao buscar tarefas pendentes:", e.message || e);
      return { processed: 0, error: e.message };
    }

    let processed = 0;
    
    for (const t of pendingTasks) {
      const canonicalTaskId = `mananciall/${t.area}/${t.project}/${t.task}`;
      console.log(`⏱️ [UNIVERSAL] Roteando task: ${canonicalTaskId} (ID: ${t.id})`);
      
      try {
        switch (canonicalTaskId) {
          case "mananciall/channels/yt_en_treasures_spurgeon/narrate-audio": {
            console.log(`🎙️ [UNIVERSAL] Disparando narrateAudio para a task ${t.id}...`);
            await narrateAudio.trigger({ recordId: t.id });
            processed++;
            break;
          }
          case "mananciall/channels/yt_en_treasures_spurgeon/transcribe-audio": {
            console.log(`🎙️ [UNIVERSAL] Disparando transcribeAudio para a task ${t.id}...`);
            await transcribeAudio.trigger({ recordId: t.id });
            processed++;
            break;
          }
          case "mananciall/produto/books/publish": {
            console.log(`🚀 [UNIVERSAL] Disparando publishMananciappBooks para a task ${t.id}...`);
            await publishMananciappBooks.trigger({ taskId: t.id });
            processed++;
            break;
          }
          case "mananciall/produto/audiobooks/migrate": {
            console.log(`🚀 [UNIVERSAL] Disparando migrateAudiobooks para a task ${t.id}...`);
            await migrateAudiobooks.trigger();
            processed++;
            break;
          }
          default: {
            if (canonicalTaskId.startsWith("mananciall/produto/") && canonicalTaskId.endsWith("/translate-content")) {
              console.log(`🌐 [UNIVERSAL] Disparando translateContent (Livro: ${t.project}) para a task ${t.id}...`);
              await translateContent.trigger({ projectIndexId: t.project });
              processed++;
            } else {
              console.warn(`⚠️ Tarefa desconhecida ou não suportada: ${canonicalTaskId}`);
            }
          }
        }
      } catch (err: any) {
        console.error(`❌ [UNIVERSAL] Erro ao disparar a tarefa ${canonicalTaskId} (ID: ${t.id}):`, err.message || err);
      }
    }
    return { processed };
  },
});
