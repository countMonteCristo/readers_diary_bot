import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, ConversationHandler

from config import Config
from db import DB
from entities import User
from handlers import (
    get_author_handlers, get_review_handlers, get_story_handlers,
    get_cancel_handler, get_fallback_handler,
)
from utils import with_db


# ENTRY POINT ------------------------------------------------------------------
@with_db
async def start(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    if update.message is None:
        return ConversationHandler.END

    text = '''Привет, {}!
Я - бот для твоего читательского дневника.
Здесь ты можешь отмечать всё, что прочитал, ставить оценки и всякое такое.
    '''.format(user.username)

    await update.message.reply_text(text)
# ------------------------------------------------------------------------------


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    # Prepare database
    Config.db().prepare()

    application = ApplicationBuilder().token(Config.token()).arbitrary_callback_data(True).build()

    fallback_handler = get_fallback_handler()
    cancel_handler = get_cancel_handler()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    author_handlers = get_author_handlers(fallback_handler, cancel_handler)
    story_handlers = get_story_handlers(fallback_handler, cancel_handler)
    review_handlers = get_review_handlers(fallback_handler, cancel_handler)

    application.add_handlers(author_handlers)
    application.add_handlers(story_handlers)
    application.add_handlers(review_handlers)

    application.run_polling()
