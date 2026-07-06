import { narrateAudio } from "./channelsyt_treasuresspurgeon/narrator";
import { transcribeAudio } from "./channelsyt_treasuresspurgeon/transcriber";
import * as dotenv from "dotenv";
import * as path from "path";
import { migrateAudiobooks } from "./mananciapp/migrate";
import { cleanContentTask } from "./mananciapp/cleanContent";

// Carrega as variáveis do .env na pasta raiz do _factorio
dotenv.config({ path: path.resolve(process.cwd(), ".env") });

interface TaskInfo {
  id: string;
  task: string;
}

async function main() {
  const jsonArg = process.argv[2];
  if (!jsonArg) {
    console.log("Nenhum dado de task fornecido.");
    return;
  }
  
  try {
    const tasks = JSON.parse(jsonArg) as TaskInfo[];
    console.log(`🚀 Disparando ${tasks.length} tasks no Trigger.dev...`);
    
    for (const t of tasks) {
      if (t.task === "mananciall/channels/yt_en_treasures_spurgeon/narrate-audio" || t.task === "Narrar Áudio") {
        console.log(`👉 Disparando Narrador para a task ${t.id}...`);
        const res = await narrateAudio.trigger({ recordId: t.id });
        console.log(`✅ Task ${t.id} disparada com Run ID: ${res.id}`);
      } else if (t.task === "mananciall/channels/yt_en_treasures_spurgeon/transcribe-audio" || t.task === "Transcrever Áudio") {
        console.log(`👉 Disparando Transcritor para a task ${t.id}...`);
        const res = await transcribeAudio.trigger({ recordId: t.id });
        console.log(`✅ Task ${t.id} disparada com Run ID: ${res.id}`);
      } else if (t.task === "mananciall/produto/audiobooks/migrate" || t.task === "mananciall/migrate-audiobooks-to-r2" || t.task === "Migrar Audiobooks") {
        console.log(`👉 Disparando Migração de Audiobooks...`);
        const res = await migrateAudiobooks.trigger();
        console.log(`✅ Task de Migração disparada com Run ID: ${res.id}`);
      } else if (t.task === "mananciall/produto/books/clean-content" || t.task === "Limpar Conteúdo") {
        console.log(`👉 Disparando Limpeza de Chunks (Llama 3.1 8B)...`);
        const res = await cleanContentTask.trigger({ limit: 1000 });
        console.log(`✅ Task de Limpeza disparada com Run ID: ${res.id}`);
      } else {
        console.warn(`⚠️ Tipo de tarefa não suportado para disparo direto: ${t.task}`);
      }
    }
  } catch (e: any) {
    console.error("❌ Falha ao processar e disparar tasks:", e.message || e);
  }
}

if (typeof process !== "undefined" && process.argv[1] && (process.argv[1].endsWith("trigger_runner.ts") || process.argv[1].endsWith("trigger_runner.js"))) {
  main();
}
