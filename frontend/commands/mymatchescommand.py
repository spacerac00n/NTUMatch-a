import logging
from datetime import datetime
from typing import List, Optional

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import CommandHandler, ContextTypes

from api_client import NTUMatchAPI

api_client = NTUMatchAPI()
logger = logging.getLogger(__name__)


def _format_match_line(match: dict) -> Optional[str]:
    matched_user = match.get("user", {}) if isinstance(match, dict) else {}
    username = matched_user.get("telegram_username")
    if not username:
        return None

    matched_at = match.get("matched_at")
    match_date = None
    if isinstance(matched_at, str):
        try:
            match_date = datetime.fromisoformat(matched_at)
        except ValueError:
            logger.debug("Unable to parse match date: %s", matched_at)
    if match_date:
        date_text = match_date.strftime("%d %b %Y")
    else:
        date_text = matched_at or "Unknown date"

    return f"• @{username} - Matched on {date_text}"


async def mymatches(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user

    if chat is None or user is None:
        return

    if not user.username:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Please set a Telegram username in your settings to use NTUMatch.",
        )
        return

    registered_user = context.user_data.get("registered_user")
    if (
        not registered_user
        or registered_user.get("telegram_username") != user.username
    ):
        registered_user = await api_client.get_user_by_telegram_username(user.username)
        if registered_user:
            context.user_data["registered_user"] = registered_user

    if not registered_user:
        await context.bot.send_message(
            chat_id=chat.id,
            text="You need to register first. Complete your profile with /start.",
        )
        return

    await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)

    matches = await api_client.get_user_matches(user.username)
    if matches is None:
        await context.bot.send_message(
            chat_id=chat.id,
            text="We couldn't retrieve your matches right now. Please try again later.",
        )
        return

    if not matches:
        await context.bot.send_message(
            chat_id=chat.id,
            text="You have no matches yet. Keep exploring profiles with /match!",
        )
        return

    lines: List[str] = ["Here are your matches:"]
    for match in matches:
        line = _format_match_line(match)
        if line:
            lines.append(line)

    if len(lines) == 1:
        lines.append("No valid match information available.")

    await context.bot.send_message(chat_id=chat.id, text="\n".join(lines))


mymatches_handler = CommandHandler("mymatches", mymatches)
