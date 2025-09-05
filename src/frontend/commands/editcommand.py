from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters
from api_client import NTUMatchAPI

# States for conversation handlers
EDIT_SELECTION, EDIT_AGE, EDIT_HOBBY, EDIT_DESCRIPTION = range(4)

api_client = NTUMatchAPI()

async def edit (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the edit process"""
    telegram_username = update.effective_user.username  
    
    # Check if user exist 
    user_data = await api_client.get_user_by_telegram_username(telegram_username)
    if not user_data:
        await update.message.reply_text("You are not registered yet. Please use /start to register.")
        return ConversationHandler.END

    reply_keyboard = [["Edit Age", "Edit Hobby"], ["Edit Description", "Cancel"]]

    await update.message.reply_text(
        "What would you like to edit?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=reply_keyboard, one_time_keyboard=True, input_field_placeholder="Choose an option", resize_keyboard=True
        ),
    )
    return EDIT_SELECTION

async def edit_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's selection for editing"""
    selection = update.message.text
    if selection == "Edit Age":
        await update.message.reply_text("Please enter your new age:", reply_markup=ReplyKeyboardRemove())
        return EDIT_AGE
    elif selection == "Edit Hobby":
        await update.message.reply_text("Please enter your new hobby:", reply_markup=ReplyKeyboardRemove())
        return EDIT_HOBBY
    elif selection == "Edit Description":
        await update.message.reply_text("Please enter your new description:", reply_markup=ReplyKeyboardRemove())
        return EDIT_DESCRIPTION
    elif selection == "Cancel":
        await update.message.reply_text("Edit cancelled.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    else:
        await update.message.reply_text("Invalid selection. Please choose again.")
        return EDIT_SELECTION

async def edit_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Edit user's age"""
    try:
        updated_age = int(update.message.text)
        if updated_age < 16 or updated_age > 30:
            await update.message.reply_text("Please enter a valid age (16-30):")
            return EDIT_AGE
        
        user_data = await api_client.get_user_by_telegram_username(update.effective_user.username)
        user_data["age"] = updated_age
        result = await api_client.update_user_by_telegram_username(
            telegram_username=update.effective_user.username,
            user_data=user_data
        )
        if result:
            await update.message.reply_text(f"Your age has been updated to {updated_age}. What else would you like to edit?", reply_markup=ReplyKeyboardRemove())
        else:
            await update.message.reply_text("Failed to update age. Please try again later.")
    except ValueError:
        await update.message.reply_text("Invalid input. Please enter a valid age (16-30):")
        return EDIT_AGE
    return await edit(update, context)

async def edit_hobby (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Edit user's hobby"""
    updated_hobby = update.message.text
    user_data = await api_client.get_user_by_telegram_username(update.effective_user.username)
    user_data["hobby"] = updated_hobby
    result = await api_client.update_user_by_telegram_username(
        telegram_username=update.effective_user.username,
        user_data=user_data
    )
    if result:
        await update.message.reply_text(f"Your hobby has been updated. What else would you like to edit?", reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text("Failed to update hobby. Please try again later.")
    return await edit(update, context)

async def edit_description (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Edit user's description"""
    updated_description = update.message.text
    user_data = await api_client.get_user_by_telegram_username(update.effective_user.username)
    user_data["description"] = updated_description
    result = await api_client.update_user_by_telegram_username(
        telegram_username=update.effective_user.username,
        user_data=user_data
    )
    if result:
        await update.message.reply_text(f"Your description has been updated. What else would you like to edit?", reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text("Failed to update description. Please try again later.")
    return await edit(update, context)

async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the edit process"""
    await update.message.reply_text("Edit process cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

edit_handler = ConversationHandler(
        entry_points=[CommandHandler("edit", edit)],
        states={
            EDIT_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_selection)],
            EDIT_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_age)],
            EDIT_HOBBY: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_hobby)],
            EDIT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_description)],
        },
        fallbacks=[CommandHandler("cancel", cancel_edit)],
    )