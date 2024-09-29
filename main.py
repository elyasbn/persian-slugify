import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from googletrans import Translator
import re

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the translator
translator = Translator()

# Load bot token from environment variable for security
TOKEN = os.getenv("SLUGIFY_BOT_TOKEN")

# Function to handle /start command
def start(update: Update, context: CallbackContext) -> None:
    # Introductory message with more details and a friendly tone
    update.message.reply_text(
        'Welcome to the Headline Translator & Slugify Bot!\n\n'
        'Send me a headline in Persian (or any other language), and I will convert it into a URL-friendly slug.\n\n'
        'Use /help for more options.'
    )

# Function to handle help command
def help_command(update: Update, context: CallbackContext) -> None:
    # Provide a more detailed help message
    update.message.reply_text(
        '/start - Start the bot and get a welcome message\n'
        '/help - Display this help message\n'
        'Simply send me a text to generate a slug!'
    )

# Function to handle user messages
def handle_message(update: Update, context: CallbackContext) -> None:
    headline = update.message.text.strip()

    # Translation and slug generation
    try:
        formatted_headline = translate_and_format(headline)

        # Provide an inline keyboard for user options (retranslate, feedback, etc.)
        keyboard = [[
            InlineKeyboardButton("Retranslate", callback_data='retranslate'),
            InlineKeyboardButton("Customize Slug", callback_data='customize')
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Reply with the formatted headline
        update.message.reply_text(
            f"Your formatted slug: \n`{formatted_headline}`",
            parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        update.message.reply_text("An error occurred. Please try again later.")

# Function to translate and format the headline
def translate_and_format(headline, separator='-'):
    try:
        # Translate the headline
        translated_text = translator.translate(headline, dest='en').text

        # Convert to lowercase and replace spaces with the separator
        slugified_text = translated_text.lower().replace(' ', separator)

        # Remove special characters except for alphanumeric and separators
        slugified_text = re.sub(r'[^a-zA-Z0-9\-]', '', slugified_text)

        return slugified_text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise e

# Callback for inline button presses
def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'retranslate':
        query.edit_message_text(text="Please send the text again for retranslation.")
    elif query.data == 'customize':
        query.edit_message_text(text="Please send the separator you'd like (e.g., '_' or '-').")

# Function to log errors
def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main() -> None:
    # Create Updater and pass bot token
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # Register message handler for text
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Register callback query handler for inline buttons
    dispatcher.add_handler(CallbackQueryHandler(button_callback))

    # Log all errors
    dispatcher.add_error_handler(error)

    # Start polling for updates
    updater.start_polling()

    # Block until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
