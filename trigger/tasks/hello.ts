import { task } from "@trigger.dev/sdk/v3";

export const ping = task({
  id: "ping",
  run: async () => {
    const now = new Date().toISOString();
    console.log(`[${now}] Factorio online — sistema autônomo operacional 🏭`);
    return { status: "ok", timestamp: now };
  },
});

export const pesquisarForeplay = task({
  id: "pesquisar-foreplay",
  run: async (payload: { termo: string; limite?: number }) => {
    const { termo, limite = 10 } = payload;
    const apiKey = process.env.FOREPLAY_API_KEY;

    if (!apiKey) throw new Error("FOREPLAY_API_KEY não configurada");

    const res = await fetch(
      `https://public.api.foreplay.co/api/discovery/ads?q=${encodeURIComponent(termo)}&limit=${limite}`,
      { headers: { Authorization: apiKey } }
    );

    if (!res.ok) throw new Error(`Foreplay API error: ${res.status}`);

    const data = await res.json();
    console.log(`🔍 Pesquisa "${termo}": ${data.metadata?.count || 0} anúncios encontrados`);
    return data;
  },
});