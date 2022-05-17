import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, ConversationHandler

from config import Config
from db import DB
from entites import User
from handlers.author import get_author_handlers
from handlers.common import get_cancel_handler
from handlers.review import get_review_handlers
from handlers.story import get_story_handlers
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

    cancel_handler = get_cancel_handler()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    author_handlers = get_author_handlers(cancel_handler)
    story_handlers = get_story_handlers(cancel_handler)
    review_handlers = get_review_handlers(cancel_handler)

    application.add_handlers(author_handlers)
    application.add_handlers(story_handlers)
    application.add_handlers(review_handlers)

    application.run_polling()
