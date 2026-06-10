import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from tools import register_all_tools
from config import HUB_HOST, HUB_PORT

mcp = FastMCP("mcp-universal", port=HUB_PORT, host=HUB_HOST)
mcp = register_all_tools(mcp)

if __name__ == "__main__":
    transport = "stdio" if "--stdio" in sys.argv else "sse"
    print(f"MCP Universal rodando em {HUB_HOST}:{HUB_PORT} (transporte: {transport})")
    if transport == "sse":
        print(f"SSE endpoint: http://{HUB_HOST}:{HUB_PORT}/sse")
    mcp.run(transport=transport)
