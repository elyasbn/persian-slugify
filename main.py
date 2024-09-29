import os
import logging
from typing import Dict, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
from telegram.constants import ParseMode
from googletrans import Translator
import re

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize the translator
translator = Translator()

# Load bot token from environment variable for security
TOKEN = os.getenv("SLUGIFY_BOT_TOKEN")

# Define conversation states
AWAITING_SEPARATOR, AWAITING_TEXT = range(2)

# User session storage
user_data: Dict[int, Dict] = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user = update.effective_user
    await update.message.reply_html(
        f"Welcome, {user.mention_html()}! 👋\n\n"
        "I'm the Headline Translator & Slugify Bot. Here's what I can do for you:\n\n"
        "🔤 Translate headlines from any language to English\n"
        "🔗 Convert headlines into URL-friendly slugs\n"
        "🛠 Customize your slugs with different separators\n\n"
        "To get started, simply send me a headline or use /help for more options."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provide help information to the user."""
    help_text = (
        "🤖 <b>Headline Translator & Slugify Bot Help</b>\n\n"
        "Here are the available commands and features:\n\n"
        "/start - Initialize the bot and get a welcome message\n"
        "/help - Display this help message\n"
        "/settings - Customize your slug preferences\n"
        "/history - View your recent translations and slugs\n\n"
        "Simply send any text to translate and slugify it!\n\n"
        "Need more help? Feel free to ask!"
    )
    await update.message.reply_html(help_text)

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /settings command."""
    keyboard = [
        [InlineKeyboardButton("Change Separator", callback_data="change_separator")],
        [InlineKeyboardButton("Reset Preferences", callback_data="reset_preferences")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📐 Settings\n\nCustomize your slugify preferences:", reply_markup=reply_markup
    )

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /history command."""
    user_id = update.effective_user.id
    if user_id not in user_data or "history" not in user_data[user_id]:
        await update.message.reply_text("You don't have any translation history yet.")
        return

    history_text = "📜 Your recent translations:\n\n"
    for item in user_data[user_id]["history"][-5:]:  # Show last 5 items
        history_text += f"Original: {item['original']}\nSlug: {item['slug']}\n\n"
    
    await update.message.reply_text(history_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user messages."""
    user_id = update.effective_user.id
    headline = update.message.text.strip()

    if user_id not in user_data:
        user_data[user_id] = {"separator": "-"}

    try:
        formatted_headline = await translate_and_format(headline, user_data[user_id]["separator"])
        
        # Store in history
        if "history" not in user_data[user_id]:
            user_data[user_id]["history"] = []
        user_data[user_id]["history"].append({"original": headline, "slug": formatted_headline})
        
        keyboard = [
            [
                InlineKeyboardButton("♻️ Retranslate", callback_data="retranslate"),
                InlineKeyboardButton("🛠 Customize", callback_data="customize"),
            ],
            [InlineKeyboardButton("📋 Copy Slug", callback_data="copy_slug")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🔤 Original: {headline}\n\n"
            f"🔗 Slug: `{formatted_headline}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,
        )
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again later.")

async def translate_and_format(headline: str, separator: str = "-") -> str:
    """Translate and format the headline."""
    try:
        translated_text = translator.translate(headline, dest="en").text
        slugified_text = translated_text.lower().replace(" ", separator)
        slugified_text = re.sub(r"[^a-zA-Z0-9\-_]", "", slugified_text)
        return slugified_text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise e

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()

    if query.data == "retranslate":
        await query.edit_message_text("🔄 Please send the text again for retranslation.")
    elif query.data == "customize":
        await query.edit_message_text("🛠 Please send the separator you'd like (e.g., '_' or '-').")
        return AWAITING_SEPARATOR
    elif query.data == "copy_slug":
        # In a real bot, you'd implement clipboard functionality here
        await query.edit_message_text("📋 Slug copied to clipboard! (simulated)")
    elif query.data == "change_separator":
        await query.edit_message_text("🔧 Please enter your preferred separator (e.g., '_' or '-'):")
        return AWAITING_SEPARATOR
    elif query.data == "reset_preferences":
        user_id = update.effective_user.id
        user_data[user_id] = {"separator": "-"}
        await query.edit_message_text("🔄 Your preferences have been reset to default.")

async def set_separator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Set the user's preferred separator."""
    user_id = update.effective_user.id
    new_separator = update.message.text.strip()

    if len(new_separator) != 1 or new_separator not in ("-", "_"):
        await update.message.reply_text("❌ Invalid separator. Please use '-' or '_'.")
        return AWAITING_SEPARATOR

    user_data[user_id]["separator"] = new_separator
    await update.message.reply_text(f"✅ Separator set to '{new_separator}'. You can now send me a headline to slugify!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text("Operation cancelled. How else can I help you?")
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    application = Application.builder().token(TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("settings", settings))
    application.add_handler(CommandHandler("history", history))

    # Message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Callback query handler
    application.add_handler(CallbackQueryHandler(button_callback))

    # Conversation handler for setting separator
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern="^customize$|^change_separator$")],
        states={
            AWAITING_SEPARATOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_separator)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
