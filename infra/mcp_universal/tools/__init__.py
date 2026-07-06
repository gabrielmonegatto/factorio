def register_all_tools(mcp):
    from tools import baserow, llm, memory, system
    mcp = baserow.register_tools(mcp)
    mcp = llm.register_tools(mcp)
    mcp = memory.register_tools(mcp)
    mcp = system.register_tools(mcp)
    return mcp
