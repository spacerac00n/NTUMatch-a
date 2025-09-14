from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from api_client import NTUMatchAPI

# States for conversation handlers
DELETE_CONFIRMATION = 0

api_client = NTUMatchAPI()

async def delete (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the delete process"""
    telegram_username = update.effective_user.username  
    
    # Check if user exist 
    user_data = await api_client.get_user_by_telegram_username(telegram_username)
    if not user_data:
        await update.message.reply_text("You are not registered yet. Please use /start to register.")
        return ConversationHandler.END
    
    reply_keyboard = [["Yes, delete my account"],
                      ["No, keep my account"]]
    
    await update.message.reply_text(
        "Are you sure you want to delete your account? This action cannot be undone.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=reply_keyboard, one_time_keyboard=True, input_field_placeholder="Choose an option", resize_keyboard=True
        ),
    )
    return DELETE_CONFIRMATION

async def delete_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's confirmation for deletion"""
    confirmation = update.message.text
    if confirmation == "Yes, delete my account":
        telegram_username = update.effective_user.username
        result = await api_client.delete_user_by_telegram_username(telegram_username)
        if result is not None:
            await update.message.reply_text("Your account has been deleted successfully.", reply_markup=ReplyKeyboardRemove())
        else:
            await update.message.reply_text("There was an error deleting your account. Please try again later.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    elif confirmation == "No, keep my account":
        await update.message.reply_text("Account deletion cancelled.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    else:
        await update.message.reply_text("Invalid selection. Please choose again.")
        return DELETE_CONFIRMATION

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation"""
    await update.message.reply_text("Operation cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

delete_handler = ConversationHandler(
    entry_points=[CommandHandler("delete", delete)],
    states={
        DELETE_CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_confirmation)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)