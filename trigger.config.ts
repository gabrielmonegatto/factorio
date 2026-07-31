import { defineConfig } from "@trigger.dev/sdk/v3";
import { syncEnvVars } from "@trigger.dev/build/extensions/core";
import { readFileSync, existsSync } from "fs";
import { resolve } from "path";

/**
 * Credenciais que as tasks precisam NA NUVEM.
 * Lista curta de propósito: só sobe o que a esteira usa, nunca o `.env` inteiro.
 * (O `.env` da fábrica tem CRLF — daí o replace \r, mina já conhecida.)
 */
const VARS_DA_ESTEIRA = [
  "TEABLE_URL",
  "TEABLE_TOKEN",
  "OPENROUTER_API_KEY",
  "GROQ_API_KEY",
  "R2_ENDPOINT",
  "R2_ACCESS_KEY_ID",
  "R2_SECRET_ACCESS_KEY",
];

function lerEnvLocal(): { name: string; value: string }[] {
  const caminho = resolve(process.cwd(), ".env");
  if (!existsSync(caminho)) return [];
  const mapa = new Map<string, string>();
  for (const linha of readFileSync(caminho, "utf-8").split("\n")) {
    const limpa = linha.replace(/\r/g, "").trim();
    if (!limpa || limpa.startsWith("#") || !limpa.includes("=")) continue;
    const i = limpa.indexOf("=");
    mapa.set(limpa.slice(0, i).trim(), limpa.slice(i + 1).trim());
  }
  return VARS_DA_ESTEIRA.filter((n) => mapa.get(n)).map((n) => ({ name: n, value: mapa.get(n)! }));
}

export default defineConfig({
  project: "proj_dsuhcyzyqgruytusyipj",
  runtime: "node",
  logLevel: "log",
  maxDuration: 300,
  machine: "small-1x",
  build: {
    extensions: [syncEnvVars(async () => lerEnvLocal())],
  },
});
