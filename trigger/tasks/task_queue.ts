import { schedules } from "@trigger.dev/sdk/v3";
import { exec } from "child_process";
import { promisify } from "util";
import * as path from "path";

const execAsync = promisify(exec);

const TEABLE_URL = process.env.TEABLE_URL || "http://localhost:3000";
const TEABLE_TOKEN = process.env.TEABLE_TOKEN;
if (!TEABLE_TOKEN) throw new Error("TEABLE_TOKEN não configurada");
const TASKS_TABLE_ID = "tblVzN1Eo8tfk7GX2CJ";

export const runQueue = async () => {
    console.log("Checking for pending tasks in Teable...");
    
    const getUrl = `${TEABLE_URL}/api/table/${TASKS_TABLE_ID}/record`;
    const headers = {
      "Authorization": `Bearer ${TEABLE_TOKEN}`,
      "Content-Type": "application/json"
    };

    try {
      const res = await fetch(getUrl, { headers });
      if (!res.ok) {
        console.error(`Failed to fetch tasks from Teable: ${res.statusText}`);
        return;
      }

      const data = (await res.json()) as { records: any[] };
      const pendingTasks = data.records.filter(r => r.fields.Status === "Pendente");

      if (pendingTasks.length === 0) {
        console.log("No pending tasks found.");
        return;
      }

      console.log(`Found ${pendingTasks.length} pending task(s).`);

      for (const taskRecord of pendingTasks) {
        const recordId = taskRecord.id;
        const instruction = taskRecord.fields.Instruction || "";
        
        console.log(`Locking task ${recordId} (Status: Em Processamento)`);
        
        // Lock the task
        const patchUrl = `${TEABLE_URL}/api/table/${TASKS_TABLE_ID}/record/${recordId}`;
        const patchRes = await fetch(patchUrl, {
          method: "PATCH",
          headers,
          body: JSON.stringify({
            record: {
              fields: {
                Status: "Em Processamento",
                Logs: "Iniciando orquestração via Trigger.dev..."
              }
            }
          })
        });

        if (!patchRes.ok) {
          console.error(`Failed to lock task ${recordId}: ${patchRes.statusText}`);
          continue;
        }

        // Path to python script
        const scriptPath = path.resolve("C:/Users/Monegatto/Desktop/EternalL/_factorio/agents/foreplay_extractor.py");
        console.log(`Executing script: python ${scriptPath} ${recordId} "${instruction}"`);

        try {
          // Execute the Python script
          // Quote the instruction argument to handle spaces and special characters
          const { stdout, stderr } = await execAsync(`python "${scriptPath}" "${recordId}" "${instruction.replace(/"/g, '\\"')}"`);
          console.log(`Task ${recordId} execution finished.`);
          console.log(`Stdout:\n${stdout}`);
          if (stderr) {
            console.error(`Stderr:\n${stderr}`);
          }
        } catch (err) {
          console.error(`Error executing task ${recordId}:`, err);
          // Try to mark task as error in Teable
          await fetch(patchUrl, {
            method: "PATCH",
            headers,
            body: JSON.stringify({
              record: {
                fields: {
                  Status: "Erro",
                  Logs: `Erro de orquestração: ${err instanceof Error ? err.message : String(err)}`
                }
              }
            })
          }).catch(e => console.error("Failed to update task status to Error:", e));
        }
      }
    } catch (error) {
      console.error("Error running task queue processor:", error);
    }
  };

export const processarFilaTasks = schedules.task({
  id: "processar-fila-tasks",
  cron: "* * * * *", // every minute
  run: runQueue
});
