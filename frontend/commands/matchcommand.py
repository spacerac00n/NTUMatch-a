import logging
from typing import Dict, Optional, Set
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from api_client import NTUMatchAPI

api_client = NTUMatchAPI()
logger = logging.getLogger(__name__)


def _get_seen_profiles(context: ContextTypes.DEFAULT_TYPE) -> Set[str]:
    seen_profiles = context.user_data.get("seen_profiles")
    if seen_profiles is None:
        seen_profiles = set()
        context.user_data["seen_profiles"] = seen_profiles
    return seen_profiles


def _format_profile_text(profile: Dict[str, Optional[str]]) -> str:
    name = profile.get("name") or "Unknown"
    age = profile.get("age") or "N/A"
    gender = profile.get("gender") or "N/A"
    hobby = profile.get("hobby") or "N/A"
    description = profile.get("description") or "N/A"

    return (
        f"Name: {name}, Age: {age}\n"
        f"Gender: {gender}\n"
        f"Hobbies: {hobby}\n"
        f"About: {description}"
    )


def _build_keyboard(target_username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🩵 ", callback_data=f"like_{target_username}"
                ),
                InlineKeyboardButton(
                    "👎🏻 ", callback_data=f"dislike_{target_username}"
                ),
            ],
            [InlineKeyboardButton("➡️ Next", callback_data="next_profile")],
        ]
    )


async def _send_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    seen_profiles = _get_seen_profiles(context)
    profile = await _fetch_random_profile(user.username, seen_profiles)

    if profile is None:
        context.user_data.pop("current_profile", None)
        await context.bot.send_message(
            chat_id=chat.id,
            text="We couldn't load a profile right now. Please try again soon.",
        )
        return

    if isinstance(profile, dict) and profile.get("error"):
        context.user_data.pop("current_profile", None)
        error_message = profile.get("error", "No profiles available right now.")
        status_code = profile.get("status_code")
        if status_code == 404:
            await context.bot.send_message(chat_id=chat.id, text=error_message)
        else:
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"⚠️ {error_message}",
            )
        return

    target_username = profile.get("telegram_username")
    if not target_username:
        context.user_data.pop("current_profile", None)
        await context.bot.send_message(
            chat_id=chat.id,
            text="Profile data is incomplete. Please try again later.",
        )
        return

    context.user_data["current_profile"] = profile
    profile_text = _format_profile_text(profile)
    keyboard = _build_keyboard(target_username)

    if profile.get("picture_id"):
        await context.bot.send_photo(
            chat_id=chat.id,
            photo=profile["picture_id"],
            caption=profile_text,
            reply_markup=keyboard,
        )
    else:
        await context.bot.send_message(
            chat_id=chat.id,
            text=profile_text,
            reply_markup=keyboard,
        )


async def _fetch_random_profile(
    user_username: str, seen_profiles: Set[str]
) -> Optional[Dict[str, Optional[str]]]:
    max_attempts = len(seen_profiles) + 5 if seen_profiles else 5

    for _ in range(max_attempts):
        profile = await api_client.get_random_profile(user_username)
        if profile is None:
            return None

        if isinstance(profile, dict) and profile.get("error"):
            return profile

        target_username = profile.get("telegram_username")
        if not target_username or target_username == user_username:
            continue

        if target_username in seen_profiles:
            continue

        return profile

    return {"error": "No more profiles available", "status_code": 404}


async def match(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.setdefault("seen_profiles", set())
    context.user_data.pop("current_profile", None)
    await _send_profile(update, context)


async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if query.message:
        await query.edit_message_reply_markup(reply_markup=None)

    if user is None or not user.username:
        if query.message:
            await query.message.reply_text(
                "Please set a Telegram username in your settings to use NTUMatch."
            )
        return

    if not query.data or not query.data.startswith("like_"):
        return

    target_username = query.data.split("_", maxsplit=1)[1]
    seen_profiles = _get_seen_profiles(context)
    seen_profiles.add(target_username)

    response = await api_client.record_interaction(user.username, target_username, "like")
    if not response:
        if query.message:
            await query.message.reply_text(
                "We couldn't record your like. Please try again later."
            )
        return

    if response.get("error") and query.message:
        await query.message.reply_text(f"⚠️ {response['error']}")
        return

    if response.get("is_match") and query.message:
        await query.message.reply_text(
            "🎉 It's a match!\n"
            f"You and @{target_username} liked each other!"
        )
        await _notify_match(context, target_username, user.username)

    await _send_profile(update, context)


async def handle_dislike(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.message:
        await query.edit_message_reply_markup(reply_markup=None)

    user = update.effective_user
    if user is None or not user.username:
        if query.message:
            await query.message.reply_text(
                "Please set a Telegram username in your settings to use NTUMatch."
            )
        return

    if not query.data or not query.data.startswith("dislike_"):
        return

    target_username = query.data.split("_", maxsplit=1)[1]
    seen_profiles = _get_seen_profiles(context)
    seen_profiles.add(target_username)

    response = await api_client.record_interaction(
        user.username, target_username, "dislike"
    )
    if response and response.get("error") and query.message:
        await query.message.reply_text(f"⚠️ {response['error']}")

    await _send_profile(update, context)


async def handle_next(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.message:
        await query.edit_message_reply_markup(reply_markup=None)

    current_profile = context.user_data.get("current_profile")
    if current_profile:
        target_username = current_profile.get("telegram_username")
        if target_username:
            seen_profiles = _get_seen_profiles(context)
            seen_profiles.add(target_username)

    await _send_profile(update, context)


async def _notify_match(
    context: ContextTypes.DEFAULT_TYPE, match_username: str, current_username: str
) -> None:
    notification = (
        "🎉 It's a match!\n"
        f"You and @{current_username} liked each other!\n"
    )
    try:
        await context.bot.send_message(chat_id=f"@{match_username}", text=notification)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Failed to send match notification to @%s: %s", match_username, exc
        )


match_handler = CommandHandler("match", match)
like_callback_handler = CallbackQueryHandler(handle_like, pattern=r"^like_")
dislike_callback_handler = CallbackQueryHandler(handle_dislike, pattern=r"^dislike_")
next_callback_handler = CallbackQueryHandler(handle_next, pattern=r"^next_profile$")
