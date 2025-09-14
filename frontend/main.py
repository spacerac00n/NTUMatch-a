from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, filters
from dotenv import load_dotenv
import os 
from commands.startcommand import start_handler
from commands.editcommand import edit_handler
from commands.deletecommand import delete_handler

import logging

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

load_dotenv()

# Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if TELEGRAM_BOT_TOKEN is None:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set.")

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    app = ApplicationBuilder().token(str(TELEGRAM_BOT_TOKEN)).build()

    # Add handlers
    app.add_handler(start_handler)
    app.add_handler(edit_handler)
    app.add_handler(delete_handler)

    # Run the bot until the user presses Ctrl-C
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()