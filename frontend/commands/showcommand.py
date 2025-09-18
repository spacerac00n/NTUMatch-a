from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler
from api_client import NTUMatchAPI

# Conversation States
SHOW_PROFILE = range(1)

api_client = NTUMatchAPI()

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show user profile information"""
    telegram_username = update.effective_user.username
    user = await api_client.get_user_by_telegram_username(telegram_username)

    if user:
        await update.message.reply_photo(photo=user.get("picture_id"))
        profile_info = (
            f"Name: {user.get('name')}\n"
            f"Age: {user.get('age')}\n"
            f"Gender: {user.get('gender')}\n"
            f"Hobby: {user.get('hobby')}\n"
            f"Description: {user.get('description')}\n"
        )
        await update.message.reply_text(profile_info, reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text("User not found.")

show_handler = ConversationHandler(
    entry_points=[CommandHandler("show", show_profile)],
    states={},
    fallbacks=[]
)
