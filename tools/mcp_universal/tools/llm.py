import json
import httpx
from config import OPENROUTER_API_KEY

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "deepseek/deepseek-chat"

_retry_count = 0

def _headers():
    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://eternall.factory",
    }

async def _call_openrouter(messages: list, model: str = DEFAULT_MODEL, temperature: float = 0.3, max_tokens: int = 4096, response_format: dict = None) -> dict:
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        body["response_format"] = response_format

    async with httpx.AsyncClient() as c:
        r = await c.post(OPENROUTER_URL, headers=_headers(), json=body, timeout=120)
        r.raise_for_status()
        data = r.json()
        usage = data.get("usage", {})
        global _retry_count
        _retry_count = 0
        return {
            "content": data["choices"][0]["message"]["content"],
            "model": data.get("model", model),
            "tokens": usage,
        }

def register_tools(mcp):

    @mcp.tool()
    async def llm_call(prompt: str, modelo: str = DEFAULT_MODEL, temperatura: float = 0.3) -> str:
        result = await _call_openrouter(
            [{"role": "user", "content": prompt}],
            model=modelo,
            temperature=temperatura,
        )
        return result["content"]

    @mcp.tool()
    async def llm_chat_json(prompt: str, modelo: str = DEFAULT_MODEL) -> dict:
        result = await _call_openrouter(
            [{"role": "user", "content": prompt}],
            model=modelo,
            response_format={"type": "json_object"},
        )
        return json.loads(result["content"])

    @mcp.tool()
    async def llm_chat_structured(prompt: str, schema: dict, modelo: str = DEFAULT_MODEL) -> dict:
        result = await _call_openrouter(
            [
                {"role": "system", "content": f"Responda estritamente no JSON schema: {json.dumps(schema)}"},
                {"role": "user", "content": prompt},
            ],
            model=modelo,
            response_format={"type": "json_object"},
        )
        return json.loads(result["content"])

    return mcp
