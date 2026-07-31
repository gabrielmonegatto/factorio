// esteiras.ts — o motor da fábrica: UMA task agendada por esteira, cada uma no seu ritmo.
//
// Substitui o `universal-cron` antigo, que:
//   1. spawnava Python (`spawn python ENOENT` na nuvem) → morreu calado por 24 dias
//   2. falava SQL bruto com `localhost:42345` → inalcançável de fora da VPS
//   3. engolia o erro e retornava `completed` → nenhum alerta jamais disparou
//
// Aqui: TS puro + REST + falha ALTA (throw) pra o alerta do Trigger.dev disparar.
//
// Divisão de trabalho (constituição, fundamento 5 — orquestrador magro, executor gordo):
//   • Trigger.dev  → agenda, auto-cura, observa, alerta, e executa o que é chamada de API
//   • VPS (systemd)→ puxa da fila o que é pesado (render ~18min, narração) e grava o progresso
//
// A independência que o Gabriel quer vem daqui: cada esteira tem cron e fila próprios.
// Esteira de vídeo travada NÃO segura a de copy.

import { schedules } from "@trigger.dev/sdk/v3";
import { listarTasks, atualizarTask, idCanonico, type Task } from "./utils/teable.ts";

/** Minutos em "Em Processamento" antes de considerar preso (regra herdada do auto_cure antigo). */
const MINUTOS_PRESO = 20;

export interface ResumoEsteira {
  esteira: string;
  total: number;
  pendente: number;
  emProcessamento: number;
  concluido: number;
  erro: number;
  curadas: number;
  legadasPresas: number;
  porEtapa: Record<string, number>;
}

function minutosDesde(iso?: string): number {
  if (!iso) return Number.POSITIVE_INFINITY;
  return (Date.now() - new Date(iso).getTime()) / 60000;
}

/**
 * Ciclo de uma esteira: lê a fila, destrava o que ficou preso, mede e reporta.
 *
 * Auto-cura só alcança registros criados via API. Os 425 legados têm `__id` inventado
 * por SQL (ex: `task_render_recXXX`), que a API do Teable recusa — quem grava neles é o
 * operário da VPS. Aqui eles são CONTADOS e reportados, nunca silenciados.
 */
export async function rodarEsteira(esteira: string): Promise<ResumoEsteira> {
  const todas = await listarTasks();
  const minhas = todas.filter((t) => t.esteira === esteira);

  const r: ResumoEsteira = {
    esteira,
    total: minhas.length,
    pendente: 0,
    emProcessamento: 0,
    concluido: 0,
    erro: 0,
    curadas: 0,
    legadasPresas: 0,
    porEtapa: {},
  };

  const falhas: string[] = [];

  for (const t of minhas) {
    if (t.status === "Pendente") r.pendente++;
    else if (t.status === "Em Processamento") r.emProcessamento++;
    else if (t.status === "Concluído") r.concluido++;
    else if (t.status === "Erro") r.erro++;

    r.porEtapa[t.etapa] = (r.porEtapa[t.etapa] ?? 0) + 1;

    const precisaCura =
      (t.status === "Em Processamento" && minutosDesde(t.modificadoEm) > MINUTOS_PRESO) ||
      t.status === "Erro";
    if (!precisaCura) continue;

    if (t.somenteLeitura) {
      r.legadasPresas++;
      continue;
    }
    try {
      const motivo =
        t.status === "Erro"
          ? "Erro → Pendente (re-tentativa automática)"
          : `preso >${MINUTOS_PRESO}min em Em Processamento → Pendente`;
      await atualizarTask(t.id, {
        Status: "Pendente",
        Logs: `${t.logs ?? ""}\n[${new Date().toISOString()}] [AUTO-CURA] ${motivo}`.trim().slice(-8000),
      });
      r.curadas++;
      console.log(`  🩹 curada ${idCanonico(t)}: ${motivo}`);
    } catch (e: any) {
      falhas.push(`${t.id}: ${e?.message ?? e}`);
    }
  }

  console.log(
    `📊 [${esteira}] total=${r.total} pendente=${r.pendente} processando=${r.emProcessamento} ` +
      `concluido=${r.concluido} erro=${r.erro} | curadas=${r.curadas} legadas-presas=${r.legadasPresas}`,
  );
  console.log(`   etapas: ${JSON.stringify(r.porEtapa)}`);

  // Falha ALTA: o cron antigo devolvia o erro como valor e ficava "completed" pra sempre.
  if (falhas.length) {
    throw new Error(`Esteira ${esteira}: ${falhas.length} falha(s) ao curar -> ${falhas.slice(0, 3).join(" | ")}`);
  }
  return r;
}

// ── Uma task agendada POR esteira ─────────────────────────────────────────────
// Cron e concorrência próprios = ritmo próprio, independência real.

export const esteiraVideo = schedules.task({
  id: "mananciall/software/factorio/esteira-video",
  cron: "*/15 * * * *",
  maxDuration: 300,
  queue: { name: "esteira-video", concurrencyLimit: 1 }, // render é pesado, um por vez
  run: async () => rodarEsteira("video"),
});

export const esteiraChannels = schedules.task({
  id: "mananciall/software/factorio/esteira-channels",
  cron: "*/15 * * * *",
  maxDuration: 300,
  queue: { name: "esteira-channels", concurrencyLimit: 1 },
  run: async () => rodarEsteira("channels"),
});

export const esteiraProduto = schedules.task({
  id: "mananciall/software/factorio/esteira-produto",
  cron: "*/30 * * * *",
  maxDuration: 300,
  queue: { name: "esteira-produto", concurrencyLimit: 2 },
  run: async () => rodarEsteira("produto"),
});
