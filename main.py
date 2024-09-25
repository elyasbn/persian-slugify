from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from googletrans import Translator
import re

# Initialize the translator
translator = Translator()

# Function to handle /start command
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Welcome to the Headline Translator Bot!\n\n'
                              'Please enter your headline in Persian.')

# Function to handle messages
def handle_message(update: Update, context: CallbackContext) -> None:
    # Get the user's message
    headline = update.message.text.strip()

    # Translate and format the headline
    formatted_headline = translate_and_format(headline)

    # Reply to the user with the formatted headline in a code block
    update.message.reply_text(f"\n{formatted_headline}\n", parse_mode=ParseMode.MARKDOWN)

# Function to translate and format the headline
def translate_and_format(headline):
    try:
        # Translate the headline to English
        english_headline = translator.translate(headline, dest='en').text

        # Convert the headline to lowercase and replace spaces with hyphens
        formatted_headline = english_headline.lower().replace(' ', '-')

        # Remove special characters except alphanumeric and hyphens
        formatted_headline = re.sub(r'[^a-zA-Z0-9\-]', '', formatted_headline)

        return formatted_headline
    except Exception as e:
        print(f"Error translating headline: {e}")
        return "Error translating headline."

def main() -> None:
    # Create the Updater and pass in your bot's token
    updater = Updater("7430957502:AAGf7y8eZpkYUTNgHmjjC4-OTl2ANP2ara8")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handler for /start
    dispatcher.add_handler(CommandHandler("start", start))

    # Register message handler
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
