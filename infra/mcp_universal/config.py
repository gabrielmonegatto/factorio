from os import getenv
from dotenv import load_dotenv

load_dotenv()

BASEROW_URL = getenv("BASEROW_URL", "http://factorio.io")
BASEROW_TOKEN = getenv("BASEROW_TOKEN", "")
BASEROW_HUB_TOKEN = getenv("BASEROW_HUB_TOKEN", "")
BASEROW_HUB_WORKSPACE_ID = int(getenv("BASEROW_HUB_WORKSPACE_ID", "160"))
OPENROUTER_API_KEY = getenv("OPENROUTER_API_KEY", "")
GEMINI_API_KEY = getenv("GEMINI_API_KEY", "")

HUB_PORT = int(getenv("MCP_HUB_PORT", "3111"))
HUB_HOST = getenv("MCP_HUB_HOST", "0.0.0.0")

TABLE_WIKI_CONCEITOS = int(getenv("TABLE_WIKI_CONCEITOS", "1522"))
TABLE_TOOLS_REGISTRY = int(getenv("TABLE_TOOLS_REGISTRY", "1523"))
TABLE_TOOLS_LOGS = int(getenv("TABLE_TOOLS_LOGS", "1524"))
TABLE_AGENT_CONFIGS = int(getenv("TABLE_AGENT_CONFIGS", "1525"))
TABLE_SYSTEM_CONFIG = int(getenv("TABLE_SYSTEM_CONFIG", "1526"))
