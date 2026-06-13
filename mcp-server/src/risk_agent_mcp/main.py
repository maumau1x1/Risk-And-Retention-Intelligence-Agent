"""Risk & Retention Intelligence — FastMCP server entrypoint."""

from __future__ import annotations

import logging

from dotenv import load_dotenv
from fastmcp import FastMCP

from risk_agent_mcp.config import get_settings
from risk_agent_mcp.tools.registry import register_tools

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

mcp = FastMCP(
    name="Risk & Retention Intelligence",
    instructions=(
        "Enterprise MCP server for risk analysts. Tools query Microsoft Fabric IQ "
        "semantic models for churn, loss recovery, and retention KPIs. "
        "Dashboard tools return interactive MCP App widgets."
    ),
)

register_tools(mcp)


def run() -> None:
    settings = get_settings()
    mcp.run(
        transport="http",
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
        path="/mcp",
    )


if __name__ == "__main__":
    run()
