"""
Weave Subsystem - Core Domain Logic & Agent Definition.
Provides WeaveAgent class, streaming transcription node filtering, prompt instructions, and toolset initialization.
"""

import contextlib
import logging
import os
import shutil
import sys
from collections.abc import AsyncGenerator, AsyncIterable
from typing import Any

from livekit.agents.llm.mcp import MCPServerStdio, MCPToolset
from livekit.agents.voice import Agent

from textile import Yarn, YarnManifest, loom
from textile.core.orchestration.instructions import fabric_instructions
from textile.core.orchestration.stream import stream_engine

logger = logging.getLogger(__name__)


class WeaveYarn(Yarn):
    """Weave Voice AI Capability Yarn managing runtime settings and LiveKit integration."""

    def __init__(self, manifest: YarnManifest | None = None) -> None:
        super().__init__(manifest=manifest)


def get_weave_settings() -> Any:
    """Retrieve validated Weave settings from active Skein/Loom instance or defaults."""
    return loom.get_settings("weave")


def prewarm_livekit_pipeline() -> None:
    """Pre-warm Fabric Loom, Pydantic schemas, NumPy FFT, and LiveKit hyphenator Tries off the asyncio loop."""
    loom.initialize()
    with contextlib.suppress(Exception):
        import numpy as np  # noqa: PLC0415

        np.fft.rfft([0.0])
    with contextlib.suppress(Exception):
        from livekit.agents.tokenize import _basic_hyphenator  # noqa: PLC0415

        _basic_hyphenator._get_hyphenator()


class WeaveAgent(Agent):
    """Voice companion agent with real-time streaming semantic token interception via Loom Wefts."""

    async def transcription_node(
        self,
        text: AsyncIterable[str | Any],
        model_settings: Any,  # noqa: ARG002
    ) -> AsyncGenerator[str | Any]:
        async for delta in text:
            delta_text = getattr(delta, "text", None) or (delta if isinstance(delta, str) else str(delta))
            clean_delta = stream_engine.process_stream(delta_text, loom.wefts)
            if clean_delta:
                if hasattr(delta, "text"):
                    setattr(delta, "text", clean_delta)
                    yield delta
                else:
                    yield clean_delta


def build_textile_toolset() -> MCPToolset:
    """Configures the isolated Textile twill MCP toolset environment."""
    textile_env = dict(os.environ)
    textile_env["TEXTILE_CALLER"] = "weave"
    textile_cmd = shutil.which("textile") or sys.executable
    textile_args = (
        ["twill"] if shutil.which("textile") else ["-c", "from textile.core.cli import main; main()", "twill"]
    )

    return MCPToolset(
        id="textile",
        mcp_server=MCPServerStdio(
            command=textile_cmd,
            args=textile_args,
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


