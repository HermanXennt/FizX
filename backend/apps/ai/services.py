from apps.chat.services import ChannelService
from apps.integrations.openai import service as openai_service
from apps.meetings.models import Meeting

PRESET_PROMPTS = {
    "summarize": "Summarize this meeting in a few clear sentences, grounded only in the context below.",
    "action_items": (
        "List the concrete action items from this meeting as a short bulleted list, grounded only in the "
        "context below. If none are clear from the available context, say so plainly instead of inventing any."
    ),
    "follow_up_email": (
        "Draft a short, friendly follow-up email to the meeting participants summarizing what was discussed, "
        "grounded only in the context below."
    ),
}


def _build_meeting_context(meeting: Meeting) -> str:
    participants = list(meeting.participants.select_related("user").all())
    spoke = [p.user.full_name for p in participants if p.has_spoken]
    quiet = [p.user.full_name for p in participants if not p.has_spoken]

    channel = ChannelService().get_or_create_meeting_channel(meeting)
    messages = list(
        channel.messages.filter(deleted_at__isnull=True).select_related("sender").order_by("-created_at")[:50]
    )
    messages.reverse()
    chat_lines = [f"{m.sender.full_name}: {m.content}" for m in messages if m.content]

    lines = [
        f"Meeting title: {meeting.title}",
        f"Host: {meeting.host.full_name}",
        f"Status: {meeting.status}",
        f"Participants who spoke: {', '.join(spoke) or 'none recorded'}",
        f"Participants who did not speak: {', '.join(quiet) or 'none'}",
    ]
    if chat_lines:
        lines.append("Chat transcript:")
        lines.extend(chat_lines)
    else:
        lines.append("Chat transcript: empty - no messages were sent in the meeting chat.")
    return "\n".join(lines)


def who_hasnt_spoken(meeting: Meeting) -> str:
    quiet = [p.user.full_name for p in meeting.participants.select_related("user").all() if not p.has_spoken]
    if not quiet:
        return "Everyone who joined this meeting spoke at some point."
    if len(quiet) == 1:
        return f"{quiet[0]} hasn't spoken yet."
    return ", ".join(quiet[:-1]) + f", and {quiet[-1]} haven't spoken yet."


def ask(*, message: str, preset: str, meeting: Meeting | None, user_name: str, user_has_live_meeting: bool) -> str:
    if preset == "who_hasnt_spoken" and meeting is not None:
        return who_hasnt_spoken(meeting)

    if meeting is not None:
        system = (
            "You are FizX's AI meeting assistant. Answer using only the meeting context provided below - "
            "never invent details that aren't in it.\n\n" + _build_meeting_context(meeting)
        )
    else:
        live_note = "They currently have a live meeting in progress." if user_has_live_meeting else (
            "They do not currently have a live meeting in progress."
        )
        system = (
            "You are FizX's AI assistant, embedded in a video conferencing app dashboard. "
            f"You're talking to {user_name}. {live_note} "
            "No specific meeting is selected, so answer generally and helpfully; if the question clearly "
            "needs a specific meeting's data you don't have, say so."
        )

    user_message = PRESET_PROMPTS.get(preset, message)
    return openai_service.ask(system=system, message=user_message)
