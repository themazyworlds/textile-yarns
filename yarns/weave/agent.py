"""
agent.py - Main LiveKit Connection Entrypoint & Server Dispatcher.
Handles AgentServer initialization, RTC session lifecycle, and runtime execution loops.
"""

from typing import Any

from livekit.agents import AgentServer, AutoSubscribe, JobContext, cli
from livekit.agents.voice import AgentSession
from livekit.plugins import google
from textile import EventUrgency, elastic, loom

from weave import WeaveAgent, build_textile_toolset, compose_system_prompt

server = AgentServer()


def broadcast_agent_state_changed(ev: Any) -> None:
    """Broadcast agent speaking/listening state updates to Elastic and Canvas."""
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


def broadcast_user_state_changed(ev: Any) -> None:
    """Broadcast user speaking/listening state updates to Elastic and Canvas."""
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


@server.rtc_session(agent_name="weave")
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    settings = loom.get_settings("weave")

    realtime_model = google.realtime.RealtimeModel(
        model=settings.model,
        voice=settings.voice,
    )

    textile_toolset = build_textile_toolset()
    await textile_toolset.setup()

    session = AgentSession(
        llm=realtime_model,
    )
    session.on("agent_state_changed", broadcast_agent_state_changed)
    session.on("user_state_changed", broadcast_user_state_changed)

    agent = WeaveAgent(
        instructions=compose_system_prompt(base_instructions=settings.instructions),
        tools=[textile_toolset],
    )

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    await session.start(room=ctx.room, agent=agent)
    await session.generate_reply(
        instructions="Say a brief, confident hello stating that desktop systems and Weave are online."
    )


if __name__ == "__main__":
    cli.run_app(server)
