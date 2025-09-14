from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from api_client import NTUMatchAPI
from commands.editcommand import edit

# Conversation States
NAME, EMAIL, AGE, GENDER, HOBBY, LOCATION, DESCRIPTION = range(7)

api_client = NTUMatchAPI()

async def start (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Check the telegram username inside the database
    telegram_username = update.effective_user.username  
    user = await api_client.get_user_by_telegram_username(telegram_username)
    if user:
        await update.message.reply_text(f"Glad to see you back, {user['name']} !")
        keyboard = [["/edit", "/delete"], ["/match"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("Choose your next action:", reply_markup=reply_markup)
        
    else:
        await update.message.reply_text("Hi, there !\nIt seems you're new here. Please register to continue.")
        await update.message.reply_text("Please enter your NTU Email Address: ")   
        return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get user's email"""
    email = update.message.text
    
    # Basic email validation
    if not email or "@" not in email or not email.endswith("ntu.edu.sg"):
        await update.message.reply_text(
            "Please enter a valid NTU email address (ending with @ntu.edu.sg):"
        )
        return EMAIL
    
    context.user_data['email'] = email

    await update.message.reply_text("Great! Now, what's your full name?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get user's full name"""
    name = update.message.text
    context.user_data['name'] = name

    await update.message.reply_text(f"Nice to meet you ! How old are you?")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get user's age"""
    try:
        age = int(update.message.text)
        if age < 16 or age > 30:
            await update.message.reply_text("Please enter a valid age (16-30):")
            return AGE
        
        context.user_data['age'] = age

        reply_keyboard = [["Male", "Female"]]

        await update.message.reply_text(
            "What's your gender?", 
            reply_markup=ReplyKeyboardMarkup(
                keyboard=reply_keyboard, one_time_keyboard=True, resize_keyboard=True,input_field_placeholder="Select your gender"
            ),
        )

        return GENDER
    
    except ValueError:
        await update.message.reply_text("Please enter a valid number for your age:")
        return AGE

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get user's gender"""
    gender = update.message.text
    context.user_data['gender'] = gender
    await update.message.reply_text(
        "Almost done! Tell me about your hobbies or interests:", 
        reply_markup=ReplyKeyboardRemove()
    )
    return HOBBY

async def get_hobby(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get user's hobby and complete registration"""
    hobby = update.message.text
    context.user_data['hobby'] = hobby

    await update.message.reply_text("Great! Now, please provide a brief description about yourself:")
    return DESCRIPTION

async def get_description (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get user's description"""
    description = update.message.text
    context.user_data['description'] = description

    # Prepare user data for API
    user_data = {
        'telegram_username': str(update.effective_user.username),
        'email': context.user_data['email'],
        'name': context.user_data['name'],
        'age': context.user_data['age'],
        'gender': context.user_data['gender'],
        'hobby': context.user_data['hobby'],
        'description': context.user_data['description']
    }
    
    # Send to API
    result = await api_client.create_user(user_data)
    
    if result:
        await update.message.reply_text(
            f"Registration successful!\n\n"
            f"Welcome to NTUMatch, {context.user_data['name']}!\n"
            f"Your profile has been created. You can now start matching with other students!"
        )
    else:
        await update.message.reply_text(
            "Registration failed. You might already be registered or there was a server error. "
            "Please try again later or contact support."
        )
    
    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the registration process"""
    await update.message.reply_text("Registration cancelled. You can start again anytime with /start")
    context.user_data.clear()
    return ConversationHandler.END

# Registration conversation handler
start_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
        GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
        HOBBY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hobby)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
    },
    fallbacks=[CommandHandler("cancel", cancel_registration)],
)