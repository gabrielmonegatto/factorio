import { task } from "@trigger.dev/sdk/v3";
import { schedules } from "@trigger.dev/sdk/v3";

export const relatorioDiario = schedules.task({
  id: "relatorio-diario",
  // Cron: todo dia às 08:00
  cron: "0 8 * * *",
  run: async () => {
    const hoje = new Date().toISOString().slice(0, 10);
    console.log(`📊 Relatório diário — ${hoje}`);
    return { data: hoje, status: "ok" };
  },
});