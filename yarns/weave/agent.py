"""
agent.py - Main LiveKit Connection Entrypoint & Server Dispatcher.
Handles AgentServer initialization, RTC session lifecycle, and runtime execution loops.
"""

from livekit.agents import AgentServer, AutoSubscribe, JobContext, cli
from livekit.agents.voice import AgentSession
from livekit.plugins import google
from textile import EventUrgency, elastic

from weave import (
    WeaveAgent,
    build_textile_toolset,
    compose_system_prompt,
    get_weave_settings,
)

server = AgentServer()


@server.rtc_session(agent_name="weave")
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    settings = get_weave_settings()

    realtime_model = google.realtime.RealtimeModel(
        model=settings.model,
        voice=settings.voice,
    )

    textile_toolset = build_textile_toolset()
    await textile_toolset.setup()

    session = AgentSession(
        llm=realtime_model,
        turn_detection="realtime_llm",
    )

    @session.on("agent_state_changed")
    def on_agent_state_changed(ev):
        raw_state = getattr(ev, "new_state", None)
        state_str = str(getattr(raw_state, "value", raw_state) or "").lower()
        talking = state_str == "speaking"
        listening = state_str == "listening"
        elastic.broadcast(
            topic="voice.state",
            source="weave",
            summary=f"Agent {state_str}",
            urgency=EventUrgency.AMBIENT,
            data={"talking": talking, "listening": listening},
            retained_slot="canvas.is_talking",
            retained_value=talking,
        )

    @session.on("user_state_changed")
    def on_user_state_changed(ev):
        raw_state = getattr(ev, "new_state", None)
        state_str = str(getattr(raw_state, "value", raw_state) or "").lower()
        user_speaking = state_str == "speaking"
        elastic.broadcast(
            topic="voice.state",
            source="weave",
            summary=f"User {state_str}",
            urgency=EventUrgency.AMBIENT,
            data={"listening": user_speaking, "talking": False},
            retained_slot="canvas.is_listening",
            retained_value=user_speaking,
        )

    agent = WeaveAgent(
        instructions=compose_system_prompt(base_instructions=settings.instructions),
        tools=[textile_toolset],
    )

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    await session.start(room=ctx.room, agent=agent)
    await session.generate_reply(
        instructions="Say a brief, confident hello stating that desktop systems and Weave are online."
    )


def run_voice_agent(*, dev: bool = False, text: bool = False) -> None:
    """Exec into `lk agent console` (or dev). The lk CLI owns audio, credentials, and the terminal UI."""
    import os
    import shutil
    from pathlib import Path

    lk_bin = shutil.which("lk")
    if not lk_bin:
        print(
            "LiveKit CLI ('lk') not found on PATH.\n"
            "Install:  curl -sSL https://get.livekit.io/cli | bash && lk cloud auth"
        )
        return

    weave_dir = Path(__file__).resolve().parent
    script_path = str(Path(__file__).resolve())

    # Set working directory to weave folder so lk detects Python agent correctly
    os.chdir(weave_dir)

    cmd = [lk_bin, "agent", "dev" if dev else "console"]
    if not dev and text:
        cmd.append("--text")
    cmd.append(script_path)

    os.execvp(lk_bin, cmd)


if __name__ == "__main__":
    cli.run_app(server)
