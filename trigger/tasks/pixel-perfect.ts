import { task } from "@trigger.dev/sdk/v3";
import { exec } from "child_process";
import { promisify } from "util";
import * as path from "path";
import * as fs from "fs";
import OpenAI from "openai";

const execAsync = promisify(exec);

const PIXEL_PERFECT_DIR = path.resolve(
  "C:/Users/Monegatto/Desktop/EternalL/_factorio/workflows/pixel_perfect"
);
const OUTPUT_DIR = path.resolve(
  "C:/Users/Monegatto/Desktop/EternalL/_factorio/outputs/pixel_perfect"
);

// ─────────────────────────────────────────────────────────────
// TIPOS
// ─────────────────────────────────────────────────────────────

interface PixelPerfectPayload {
  /** URL completa da página a ser clonada */
  url: string;
  /** Nome amigável para a pasta de output (ex: "landing-produto-x") */
  nome?: string;
  /** Modelo OpenAI a usar na reconstrução (default: gpt-4o) */
  modelo?: string;
  /** Se true, pula a fase de QA visual */
  skipQa?: boolean;
}

// ─────────────────────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────────────────────

function slugify(url: string): string {
  return url
    .replace(/^https?:\/\//, "")
    .replace(/[^a-z0-9]/gi, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
    .toLowerCase()
    .slice(0, 60);
}

async function runScript(script: string, args: string[]): Promise<string> {
  const cmd = `node "${path.join(PIXEL_PERFECT_DIR, script)}" ${args.join(" ")}`;
  console.log(`▶ ${cmd}`);
  const { stdout, stderr } = await execAsync(cmd, {
    cwd: PIXEL_PERFECT_DIR,
    timeout: 180_000,
  });
  if (stdout) console.log(stdout);
  if (stderr) console.error(stderr);
  return stdout;
}

// ─────────────────────────────────────────────────────────────
// AGENTE DE RECONSTRUÇÃO (OpenAI)
// Usa tool calls para escrever arquivos no disco diretamente.
// ─────────────────────────────────────────────────────────────

const SYSTEM_PROMPT = `Você é um especialista em Astro e CSS que reconstrói páginas web com máxima fidelidade visual (pixel-perfect).

Você recebe um documento com:
- Metadados da página (título, idioma, descrição)
- Paleta de cores e tipografia extraídas
- CSS computado real de cada elemento (não o CSS bruto — o CSS real aplicado pelo browser)
- Mapa de assets locais (imagens, fontes)
- HTML da página original

Sua tarefa é reconstruir a página como um projeto Astro completo.

REGRAS OBRIGATÓRIAS:
1. Use os valores EXATOS de CSS extraídos (font-size, padding, margin, colors, etc)
2. Crie componentes .astro separados para cada seção principal (Hero, Header, Footer, CTA, etc)
3. Declare design tokens como CSS custom properties no :root global
4. Referencie assets pelos caminhos locais do assets-map (não URLs externas)
5. O layout deve funcionar em: 1920px, 1440px, 768px, 390px
6. Use <style> scoped em cada componente Astro
7. O arquivo principal é src/pages/index.astro
8. Não use frameworks JS (React, Vue) — apenas Astro + CSS puro

Use a ferramenta write_file para criar TODOS os arquivos do projeto.
Crie no mínimo: astro.config.mjs, package.json, src/pages/index.astro, src/styles/global.css, e os componentes necessários.`;

const tools: OpenAI.Chat.ChatCompletionTool[] = [
  {
    type: "function",
    function: {
      name: "write_file",
      description: "Escreve um arquivo no disco dentro do projeto Astro",
      parameters: {
        type: "object",
        properties: {
          filepath: {
            type: "string",
            description: "Caminho relativo ao projeto Astro (ex: src/pages/index.astro)",
          },
          content: {
            type: "string",
            description: "Conteúdo completo do arquivo",
          },
        },
        required: ["filepath", "content"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "done",
      description: "Sinaliza que todos os arquivos foram criados",
      parameters: {
        type: "object",
        properties: {
          summary: {
            type: "string",
            description: "Resumo do que foi criado e observações sobre a reconstrução",
          },
          filesCreated: {
            type: "array",
            items: { type: "string" },
            description: "Lista dos arquivos criados",
          },
        },
        required: ["summary", "filesCreated"],
      },
    },
  },
];

async function runReconstructionAgent(
  outputPath: string,
  modelo: string
): Promise<{ filesCreated: string[]; summary: string }> {
  const promptPath = path.join(outputPath, "reconstruction-prompt.md");
  if (!fs.existsSync(promptPath)) {
    throw new Error(`reconstruction-prompt.md não encontrado em: ${outputPath}`);
  }

  const reconstructionPrompt = fs.readFileSync(promptPath, "utf-8");
  const astroProjectPath = path.join(outputPath, "astro-project");
  fs.mkdirSync(astroProjectPath, { recursive: true });

  const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

  const messages: OpenAI.Chat.ChatCompletionMessageParam[] = [
    { role: "system", content: SYSTEM_PROMPT },
    {
      role: "user",
      content: `Reconstrua essa página como projeto Astro. Escreva TODOS os arquivos usando write_file, depois chame done.\n\n${reconstructionPrompt}`,
    },
  ];

  const filesCreated: string[] = [];
  let summary = "";
  let iterations = 0;
  const MAX_ITERATIONS = 20; // evita loop infinito

  console.log(`🤖 Agente de reconstrução iniciado (modelo: ${modelo})`);

  while (iterations < MAX_ITERATIONS) {
    iterations++;

    const response = await openai.chat.completions.create({
      model: modelo,
      messages,
      tools,
      tool_choice: "auto",
      max_tokens: 16000,
    });

    const choice = response.choices[0];
    const message = choice.message;

    // Adiciona resposta do modelo ao histórico
    messages.push(message);

    // Sem tool calls → modelo terminou sem chamar done
    if (!message.tool_calls || message.tool_calls.length === 0) {
      console.log("⚠️ Agente terminou sem chamar done. Encerrando.");
      break;
    }

    // Processa cada tool call
    const toolResults: OpenAI.Chat.ChatCompletionMessageParam = {
      role: "tool" as const,
      // será sobrescrito abaixo para múltiplos
      tool_call_id: message.tool_calls[0].id,
      content: "",
    };

    // Para múltiplos tool calls, adiciona cada resultado separado
    for (const toolCall of message.tool_calls) {
      const args = JSON.parse(toolCall.function.arguments) as Record<string, unknown>;

      if (toolCall.function.name === "write_file") {
        const filepath = args.filepath as string;
        const content = args.content as string;
        const fullPath = path.join(astroProjectPath, filepath);

        fs.mkdirSync(path.dirname(fullPath), { recursive: true });
        fs.writeFileSync(fullPath, content, "utf-8");

        filesCreated.push(filepath);
        console.log(`  📄 Criado: ${filepath}`);

        messages.push({
          role: "tool",
          tool_call_id: toolCall.id,
          content: `✅ Arquivo criado: ${filepath}`,
        });
      } else if (toolCall.function.name === "done") {
        summary = args.summary as string;
        console.log(`\n✅ Agente finalizou. ${filesCreated.length} arquivos criados.`);
        console.log(`   Resumo: ${summary}`);
        return { filesCreated, summary };
      }
    }

    // Continua o loop para o próximo round de tool calls
  }

  return { filesCreated, summary: `Concluído após ${iterations} iterações.` };
}

// ─────────────────────────────────────────────────────────────
// TASK PRINCIPAL: pixel-perfect
// ─────────────────────────────────────────────────────────────

/**
 * 🎯 pixel-perfect
 *
 * Pipeline completo: extrai qualquer URL e reconstrói como projeto Astro.
 * Totalmente autônomo — nenhuma intervenção manual necessária.
 *
 * Uso no dashboard:
 *  { "url": "https://exemplo.com", "nome": "landing-x" }
 */
export const pixelPerfect = task({
  id: "pixel-perfect",
  maxDuration: 900,
  run: async (payload: PixelPerfectPayload) => {
    const { url, nome, modelo = "gpt-4o", skipQa = false } = payload;

    if (!url) throw new Error("Campo obrigatório: url");

    const slug = nome ?? slugify(url);
    const outputPath = path.join(OUTPUT_DIR, slug);
    fs.mkdirSync(outputPath, { recursive: true });

    console.log(`\n🎯 PIXEL PERFECT PIPELINE`);
    console.log(`   URL    : ${url}`);
    console.log(`   Slug   : ${slug}`);
    console.log(`   Modelo : ${modelo}`);
    console.log(`   Output : ${outputPath}\n`);

    // ── FASE 1: EXTRAÇÃO ──────────────────────────────────────
    console.log("📐 [1/5] Extraindo DOM, CSS computado e screenshots...");
    await runScript("extract.js", [`"${url}"`, `"${outputPath}"`]);
    console.log("✅ Extração concluída\n");

    // ── FASE 2: DOWNLOAD DE ASSETS ────────────────────────────
    console.log("📦 [2/5] Baixando assets (imagens, fontes, ícones)...");
    await runScript("download-assets.js", [`"${outputPath}"`]);
    console.log("✅ Assets baixados\n");

    // ── FASE 3: GERA PROMPT ───────────────────────────────────
    console.log("📝 [3/5] Gerando contexto de reconstrução...");
    await runScript("generate-prompt.js", [`"${outputPath}"`]);
    console.log("✅ Prompt gerado\n");

    // ── FASE 4: AGENTE DE RECONSTRUÇÃO (OpenAI) ───────────────
    console.log("🤖 [4/5] Agente reconstruindo projeto Astro...");
    const { filesCreated, summary } = await runReconstructionAgent(outputPath, modelo);
    console.log(`✅ Astro gerado: ${filesCreated.length} arquivos\n`);

    // ── FASE 5: QA VISUAL ────────────────────────────────────
    if (!skipQa) {
      const astroDist = path.join(outputPath, "astro-project", "dist");
      console.log("🔍 [5/5] Rodando QA visual...");
      try {
        // Instala deps do projeto Astro gerado
        await execAsync("npm install", {
          cwd: path.join(outputPath, "astro-project"),
          timeout: 120_000,
        });
        await runScript("qa.js", [`"${url}"`, `"${outputPath}"`]);
        console.log("✅ QA concluído — veja qa-report/\n");
      } catch (err) {
        console.warn(`⚠️ QA falhou: ${(err as Error).message}`);
      }
    } else {
      console.log("⏭️  [5/5] QA pulado (skipQa: true)\n");
    }

    return {
      status: "complete",
      url,
      slug,
      outputPath,
      filesCreated,
      summary,
    };
  },
});

// ─────────────────────────────────────────────────────────────
// TASK: pixel-perfect-qa (standalone)
// ─────────────────────────────────────────────────────────────

/**
 * 🔍 pixel-perfect-qa
 *
 * Roda apenas o diff visual sobre um projeto Astro já existente.
 *
 * Uso: { "url": "https://original.com", "slug": "landing-x" }
 */
export const pixelPerfectQa = task({
  id: "pixel-perfect-qa",
  maxDuration: 180,
  run: async (payload: { url: string; slug: string }) => {
    const { url, slug } = payload;
    const outputPath = path.join(OUTPUT_DIR, slug);

    console.log(`\n🔍 QA VISUAL`);
    console.log(`   URL   : ${url}`);
    console.log(`   Slug  : ${slug}\n`);

    // Instala deps se necessário
    const astroProject = path.join(outputPath, "astro-project");
    if (fs.existsSync(path.join(astroProject, "package.json"))) {
      await execAsync("npm install", { cwd: astroProject, timeout: 120_000 });
    }

    await runScript("qa.js", [`"${url}"`, `"${outputPath}"`]);

    const reportPath = path.join(outputPath, "qa-report", "report.json");
    const report = fs.existsSync(reportPath)
      ? (JSON.parse(fs.readFileSync(reportPath, "utf-8")) as Record<string, unknown>)
      : {};

    console.log("\n📊 Resultado:");
    console.log(JSON.stringify(report, null, 2));

    return { status: "qa-complete", slug, report };
  },
});
