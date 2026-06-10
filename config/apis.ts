// 🏭 Factorio — API Registry Centralizado
// Toda API usada pela fábrica deve ser registrada aqui + no .env

export interface ApiEntry {
  key: string;
  description: string;
  service: string;
  endpoint?: string;
  docUrl?: string;
}

export const API_REGISTRY: Record<string, ApiEntry> = {
  OPENAI_API_KEY: {
    key: "OPENAI_API_KEY",
    description: "LLM principal para agentes via OpenAI SDK",
    service: "OpenAI",
    endpoint: "https://api.openai.com/v1",
    docUrl: "https://platform.openai.com/api-keys",
  },
  GEMINI_API_KEY: {
    key: "GEMINI_API_KEY",
    description: "LLM alternativo (Google Gemini)",
    service: "Google AI",
    docUrl: "https://aistudio.google.com/apikey",
  },
  ANTHROPIC_API_KEY: {
    key: "ANTHROPIC_API_KEY",
    description: "LLM alternativo (Claude)",
    service: "Anthropic",
    endpoint: "https://api.anthropic.com/v1",
    docUrl: "https://console.anthropic.com/settings/keys",
  },
  OPENROUTER_API_KEY: {
    key: "OPENROUTER_API_KEY",
    description: "Roteador de LLMs multi-provedor",
    service: "OpenRouter",
    endpoint: "https://openrouter.ai/api/v1",
    docUrl: "https://openrouter.ai/keys",
  },
  FIRECRAWL_API_KEY: {
    key: "FIRECRAWL_API_KEY",
    description: "Web scraping e crawling",
    service: "Firecrawl",
    docUrl: "https://firecrawl.dev",
  },
  FOREPLAY_API_KEY: {
    key: "FOREPLAY_API_KEY",
    description: "Pesquisa de anúncios e métricas",
    service: "Foreplay",
    docUrl: "https://foreplay.co",
  },
  TEABLE_TOKEN: {
    key: "TEABLE_TOKEN",
    description: "Autenticação Teable (banco de dados)",
    service: "Teable",
    docUrl: "https://teable.io",
  },
  ASSEMBLYAI_API_KEY: {
    key: "ASSEMBLYAI_API_KEY",
    description: "Transcrição de áudio/vídeo",
    service: "AssemblyAI",
    docUrl: "https://assemblyai.com",
  },
  PEXELS_API_KEY: {
    key: "PEXELS_API_KEY",
    description: "Banco de imagens e vídeos stock",
    service: "Pexels",
    docUrl: "https://pexels.com/api",
  },
  BASEROW_TOKEN: {
    key: "BASEROW_TOKEN",
    description: "Autenticação Baserow (banco low-code)",
    service: "Baserow",
    docUrl: "https://baserow.io",
  },
};

export function validateEnv() {
  const missing: string[] = [];
  for (const [key] of Object.entries(API_REGISTRY)) {
    if (!process.env[key]) {
      missing.push(key);
    }
  }
  if (missing.length > 0) {
    console.warn(`⚠️ APIs faltando no .env: ${missing.join(", ")}`);
  }
  return missing;
}