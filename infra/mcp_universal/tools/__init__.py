def register_all_tools(mcp):
    from tools import teable, cloudflare, runpod, memory, system
    mcp = teable.register_tools(mcp)
    mcp = cloudflare.register_tools(mcp)
    mcp = runpod.register_tools(mcp)
    mcp = memory.register_tools(mcp)
    mcp = system.register_tools(mcp)
    return mcp
