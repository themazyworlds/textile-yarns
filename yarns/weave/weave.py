"""
Weave Subsystem - Core Domain Logic & Agent Definition.
Provides WeaveAgent class, streaming transcription node filtering, prompt instructions, and toolset initialization.
"""

import contextlib
import os
import shutil
import subprocess
from collections.abc import AsyncGenerator, AsyncIterable
from pathlib import Path
from typing import Any

from livekit.agents import llm
from livekit.agents.llm.mcp import MCPServerStdio, MCPToolset
from livekit.agents.voice import Agent
from reasoning import run_reasoning_task

from textile import Yarn, fabric_instructions, loom, strand, stream_engine


class WeaveYarn(Yarn):
    """Weave Voice AI Capability Yarn managing runtime settings and LiveKit integration."""

    @strand(tier="privileged", no_timeout=True, isolated=False)
    def run_weave(self, dev: bool = False, text: bool = False) -> str:
        """Launch Weave real-time voice & desktop companion.

        :param dev: Enable developer mode with automatic reload on file changes.
        :param text: Enable text-only mode (console prompt without mic/speaker audio).
        """
        lk_bin = shutil.which("lk")
        if not lk_bin:
            return (
                "Error: LiveKit CLI ('lk') not found on PATH.\n"
                "Install: curl -sSL https://get.livekit.io/cli | bash && lk cloud auth"
            )

        weave_dir = Path(__file__).resolve().parent
        agent_file = weave_dir / "agent.py"
        if not agent_file.exists():
            return f"Error: Agent entrypoint not found at {agent_file}"

        cmd = [lk_bin, "agent", "dev" if dev else "console"]
        if not dev and text:
            cmd.append("--text")
        cmd.append("agent.py")

        env = dict(os.environ)
        curr: Path | None = weave_dir
        while curr and curr != curr.parent:
            candidate = curr / ".venv"
            if candidate.is_dir():
                env["VIRTUAL_ENV"] = str(candidate)
                env["PATH"] = f"{candidate / 'bin'}:{env.get('PATH', '')}"
                break
            curr = curr.parent

        with contextlib.suppress(KeyboardInterrupt):
            subprocess.run(cmd, cwd=str(weave_dir), env=env, check=False)
        return "Weave voice session terminated."


class WeaveAgent(Agent):
    """Voice companion agent with real-time streaming semantic token interception via Loom Wefts."""

    async def transcription_node(
        self,
        text: AsyncIterable[str | Any],
        _model_settings: Any,
    ) -> AsyncGenerator[str | Any]:
        async for delta in text:
            delta_text = getattr(delta, "text", None) or (
                delta if isinstance(delta, str) else str(delta)
            )
            clean_delta = stream_engine.process_stream(delta_text, loom.wefts)
            if clean_delta:
                if isinstance(delta, str):
                    yield clean_delta
                else:
                    try:
                        delta.text = clean_delta
                        yield delta
                    except AttributeError, TypeError:
                        yield clean_delta


@llm.function_tool(
    description=(
        "Delegate complex multi-step reasoning, system diagnosis, window management, or desktop investigation "
        "to the Pydantic AI deep reasoning backend."
    )
)
async def reason_and_execute(task: str) -> str:
    """Delegate complex multi-step reasoning to the Pydantic AI backend."""
    return await run_reasoning_task(task)


def build_textile_toolset() -> MCPToolset:
    """Configures the isolated Textile twill MCP toolset environment."""
    textile_env = dict(os.environ)
    textile_env["TEXTILE_CALLER"] = "weave"

    return MCPToolset(
        id="textile",
        mcp_server=MCPServerStdio(
            command="uv",
            args=["run", "textile", "twill"],
            env=textile_env,
            client_session_timeout_seconds=60.0,
        ),
    )


def compose_system_prompt(base_instructions: str | None = None) -> str:
    """Compose complete LLM system prompt combining base personality instructions and active fabric capabilities."""
    if base_instructions is not None:
        base = base_instructions
    else:
        settings = loom.get_settings("weave")
        base = getattr(settings, "instructions", "") if settings is not None else ""
    fabric_context = fabric_instructions.build_instructions(loom.active_yarns)
    return f"{base}\n\n{fabric_context}".strip()
