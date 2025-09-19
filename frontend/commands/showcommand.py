from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler
from api_client import NTUMatchAPI

# Conversation States
SHOW_PROFILE = range(1)

api_client = NTUMatchAPI()

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display user's profile with photo and data in a single message"""
    telegram_username = update.effective_user.username
    
    try:
        # Get user data from API
        user = await api_client.get_user_by_telegram_username(telegram_username)
        
        if not user:
            await update.message.reply_text("❌ No profile found. Please register first using /start")
            return
        
        # Format the profile information
        profile_text = (
            f"👤 **{user['name']}**, {user['age']}\n"
            f"🎯 Hobbies: {user['hobby']}\n"
            f"📝 About me: {user['description']}"
        )
        
        # Send photo with caption containing all profile data
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=user['picture_id'],  # This should be the file_id stored in your database
            caption=profile_text,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(
            "❌ Error retrieving profile. Please try again later or contact support."
        )
        # Optional: Add logging here
        print(f"Error in show_profile: {e}")

# Add this to your main bot handler
show_handler = CommandHandler("show", show_profile)
