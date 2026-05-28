"""FastMCP server montado como sub-app HTTP Streamable en /mcp."""
from __future__ import annotations

from fastmcp import FastMCP

from brain.mcp.tools import register_tools


def build_mcp(state) -> FastMCP:
    mcp = FastMCP(name="brain")
    register_tools(mcp, state)
    return mcp
