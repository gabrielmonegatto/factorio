import { task } from "@trigger.dev/sdk/v3";
import { getPythonPath, execFileAsync } from "../utils/pythonHelper";
import * as path from "path";
import * as fs from "fs";
import OpenAI from "openai";


interface MarketingPayload {
  recordId: string;
}

interface MarketingMeta {
  marketingTitle: string;
  hookText: string;
  outroText: string;
}

export async function runGenerateMarketing(payload: MarketingPayload) {
  const { recordId } = payload;
  console.log(`💡 [marketing] Iniciando geração de textos de marketing para: ${recordId}`);

  // 1. Obtém dados do banco de dados sobre o sermão
  const dbHelperPath = path.resolve(__dirname, '../scripts/render_db.py');
  const pythonCmd = getPythonPath();
  const { stdout } = await execFileAsync(pythonCmd, [dbHelperPath, "--record-id", recordId, "--get-info"]);
  const info = JSON.parse(stdout.trim());
  
  const { sermonDir, transcriptPath, sermonTitle } = info;
  
  const metaPath = path.join(sermonDir, "marketing_meta.json");
  
  // Se já existe marketing_meta.json, lê e retorna direto
  if (fs.existsSync(metaPath)) {
    console.log(`💡 [marketing] Metadados de marketing já existem localmente em: ${metaPath}`);
    const existingMeta = JSON.parse(fs.readFileSync(metaPath, "utf-8"));
    return { ...info, ...existingMeta };
  }

  if (!fs.existsSync(transcriptPath)) {
    throw new Error(`Arquivo de transcrição não encontrado em: ${transcriptPath}. Por favor, certifique-se de que a task de transcrição concluiu.`);
  }

  // 2. Lê a transcrição
  const transcriptData = JSON.parse(fs.readFileSync(transcriptPath, "utf-8"));
  const sermonText = transcriptData.text;

  if (!sermonText) {
    throw new Error("O texto da transcrição está vazio.");
  }

  // 3. Inicializa o cliente OpenAI apontando para o OpenRouter
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    throw new Error("Variável de ambiente OPENROUTER_API_KEY não configurada no Trigger.dev.");
  }

  console.log("💡 [marketing] Chamando OpenRouter (Gemini-2.5-flash) para criar ganchos de marketing...");
  const openai = new OpenAI({
    apiKey,
    baseURL: "https://openrouter.ai/api/v1",
  });

  const response = await openai.chat.completions.create({
    model: "google/gemini-2.5-flash",
    response_format: { type: "json_object" },
    messages: [
      {
        role: "system",
        content: `You are a professional video editor and copywriter specialized in Christian content.
Your task is to create marketing assets for a YouTube video based on a sermon transcript by Charles Spurgeon.
You must output a JSON object containing exactly three fields:
1. "marketingTitle": A compelling, catchy, and deep title for the video (under 70 characters). It must capture the core theme of the sermon (e.g. "The Only Safe Harbor in a World That Never Stops Changing").
2. "hookText": A short, high-retention hook script (approx. 20-30 seconds, 60-80 words). It should start with dramatic or thought-provoking questions addressing the listener directly, introducing Spurgeon's quote or sermon theme. Do not include labels, speaker tags, or scene descriptions. Only include the narrated text.
3. "outroText": A short reflection outro script (approx. 20-30 seconds, 60-85 words). It should summarize the core hope/truth of the sermon, then guide the listener to take action (subscribe, like, scan the QR code on screen to see Spurgeon's books/devotionals). Do not include labels or scene descriptions. Only include the narrated text.

Example JSON output:
{
  "marketingTitle": "The Only Safe Harbor in a World That Never Stops Changing",
  "hookText": "Are you weary of a world that shifts like sand beneath your feet? Does the relentless change in life leave you feeling unstable and afraid? Today, we dive deep into the timeless words of Charles Spurgeon on the immutability of God.",
  "outroText": "Before you leave, remember that every storm in your life is subject to the anchor of God's immutability. If you found comfort in Spurgeon's words today, take a moment to subscribe, turn on notifications. Scan the QR code on your screen to explore our collection of books."
}`
      },
      {
        role: "user",
        content: `Sermon Title: ${sermonTitle}\n\nSermon Transcript:\n${sermonText}`
      }
    ]
  });

  const responseText = response.choices[0].message.content;
  if (!responseText) {
    throw new Error("Resposta da LLM está vazia.");
  }

  const marketingMeta = JSON.parse(responseText) as MarketingMeta;
  
  // Salva no diretório do sermão
  fs.writeFileSync(metaPath, JSON.stringify(marketingMeta, null, 2), "utf-8");
  console.log(`💡 [marketing] Metadados de marketing gerados e salvos com sucesso em: ${metaPath}`);

  return { ...info, ...marketingMeta };
}

interface NarrateMarketingPayload {
  recordId: string;
  sermonDir: string;
  hookText: string;
  outroText: string;
}

export async function runNarrateMarketing(payload: NarrateMarketingPayload) {
  const { recordId, sermonDir, hookText, outroText } = payload;
  console.log(`🎙️ [marketing] Iniciando narração Kokoro para ganchos de marketing: ${recordId}`);

  const hookWavPath = path.join(sermonDir, "hook.wav");
  const ctaWavPath = path.join(sermonDir, "cta_narration.wav");

  const ttsScript = path.resolve(__dirname, '../scripts/tts_kokoro.py');
  const tempDir = path.resolve(__dirname, '../../temp');
  fs.mkdirSync(tempDir, { recursive: true });

  const pythonCmd = getPythonPath();

  // 1. Gera hook.wav se não existir
  if (!fs.existsSync(hookWavPath)) {
    console.log(`🎙️ [marketing] Gerando hook.wav...`);
    const tempHookTxt = path.join(tempDir, `hook_${recordId}.txt`);
    fs.writeFileSync(tempHookTxt, hookText, "utf-8");
    
    await execFileAsync(pythonCmd, [
      ttsScript,
      "--input", tempHookTxt,
      "--output", hookWavPath,
      "--voice", "bm_george",
      "--speed", "0.9",
      "--silence", "1.0"
    ]);
    
    if (fs.existsSync(tempHookTxt)) {
      fs.unlinkSync(tempHookTxt);
    }
  } else {
    console.log(`🎙️ [marketing] hook.wav já existe.`);
  }

  // 2. Gera cta_narration.wav se não existir
  if (!fs.existsSync(ctaWavPath)) {
    console.log(`🎙️ [marketing] Gerando cta_narration.wav...`);
    const tempCtaTxt = path.join(tempDir, `cta_${recordId}.txt`);
    fs.writeFileSync(tempCtaTxt, outroText, "utf-8");
    
    await execFileAsync(pythonCmd, [
      ttsScript,
      "--input", tempCtaTxt,
      "--output", ctaWavPath,
      "--voice", "bm_george",
      "--speed", "0.9",
      "--silence", "1.0"
    ]);
    
    if (fs.existsSync(tempCtaTxt)) {
      fs.unlinkSync(tempCtaTxt);
    }
  } else {
    console.log(`🎙️ [marketing] cta_narration.wav já existe.`);
  }

  console.log(`🎙️ [marketing] Narração de marketing concluída com sucesso!`);
  return { success: true };
}

export const generateMarketing = task({
  id: "mananciall/channels/yt_en_treasures_spurgeon/generate-marketing",
  maxDuration: 600, // 10 minutos
  run: runGenerateMarketing,
});

export const narrateMarketing = task({
  id: "mananciall/channels/yt_en_treasures_spurgeon/narrate-marketing",
  maxDuration: 600, // 10 minutos
  queue: {
    name: "channelsyt_treasuresspurgeon-narrate-queue",
    concurrencyLimit: 1, // Mesma fila e concorrência que o narrador principal para evitar sobrecarga
  },
  run: runNarrateMarketing,
});
