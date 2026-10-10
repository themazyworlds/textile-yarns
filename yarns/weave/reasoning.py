"""
reasoning.py - Pydantic AI Deep Reasoning Engine for Weave Voice Agent.
Provides strongly-typed multi-step execution, dynamic desktop context injection,
and automatic self-correcting tool retries over MCP.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPToolset, StdioTransport


class DesktopContext(BaseModel):
    """Dynamic snapshot of the active Linux desktop session."""

    user: str = Field(default_factory=lambda: os.getenv("USER", "user"))
    active_window: str | None = None
    active_workspace: str | int | None = None
    recent_errors: list[str] = Field(default_factory=list)


def create_textile_mcp_toolset() -> MCPToolset:
    """Create a Pydantic AI MCPToolset connected to Textile Twill stdio server."""
    textile_env = dict(os.environ)
    textile_env["TEXTILE_CALLER"] = "weave_reasoning"
    transport = StdioTransport(
        command="uv",
        args=["run", "textile", "twill"],
        env=textile_env,
    )
    return MCPToolset(
        transport,
        tool_error_behavior="retry",
        max_retries=2,
    )


def create_reasoning_agent(
    model_name: str = "google-gla:gemini-2.5-flash",
) -> Agent[DesktopContext, str]:
    """Create and configure the Pydantic AI reasoning agent with native Textile MCP toolset."""
    toolset = create_textile_mcp_toolset()
    agent: Agent[DesktopContext, str] = Agent(
        model_name,
        toolsets=[toolset],
        deps_type=DesktopContext,
        system_prompt=(
            "You are the deep reasoning and desktop orchestration backend for Textile Weave on Linux. "
            "You execute complex multi-step desktop diagnosis, window management, and hardware tasks "
            "using Textile MCP tools. Always produce concise, accurate summaries suitable for voice speech synthesis."
        ),
    )

    @agent.system_prompt
    def inject_dynamic_desktop_context(ctx: RunContext[DesktopContext]) -> str:
        hints = [f"Active User: {ctx.deps.user}"]
        if ctx.deps.active_window:
            hints.append(f"Focused Window: {ctx.deps.active_window}")
        if ctx.deps.active_workspace:
            hints.append(f"Active Workspace: {ctx.deps.active_workspace}")
        if ctx.deps.recent_errors:
            hints.append(f"Recent System Errors: {'; '.join(ctx.deps.recent_errors[-3:])}")
        return "\n".join(hints)

    return agent


async def run_reasoning_task(
    task: str,
    context: DesktopContext | None = None,
    model_name: str = "google-gla:gemini-2.5-flash",
) -> str:
    """Execute a complex reasoning task with dynamic desktop dependency injection."""
    ctx = context or DesktopContext()
    agent = create_reasoning_agent(model_name)
    result = await agent.run(task, deps=ctx)
    return result.data
