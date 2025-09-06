import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# === PLACEHOLDERS ===
BOT_TOKEN = "TOKENN"   # <-- Replace with your bot token
DB_PATH = " XX "         # SQLite DB file

# === SETUP DB ===
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            photo_file_id TEXT
        )
    """)
    conn.commit()
    conn.close()

# === COMMAND: START ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! Please send me your photo to register."
    )

# === HANDLE PHOTO UPLOAD ===
async def save_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo = update.message.photo[-1]  # largest size
    file_id = photo.file_id

    # Save/update file_id in DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, photo_file_id)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET photo_file_id=excluded.photo_file_id
    """, (user_id, file_id))
    conn.commit()
    conn.close()

    await update.message.reply_text("✅ Your photo has been saved! Use /show to view it.")

# === COMMAND: SHOW PHOTO ===
async def show_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT photo_file_id FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result and result[0]:
        await update.message.reply_photo(result[0], caption="Here is your saved photo 📷")
    else:
        await update.message.reply_text("⚠️ No photo found. Please upload one first!")

# === COMMAND: RESUBMIT ===
async def resubmit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📤 Please send me your new photo, it will replace the old one.")

# === MAIN ===
def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("show", show_photo))
    app.add_handler(CommandHandler("resubmit", resubmit))
    app.add_handler(MessageHandler(filters.PHOTO, save_photo))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

