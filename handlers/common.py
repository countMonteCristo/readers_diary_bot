from db import DB
from entites import User
from utils import with_db

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, ConversationHandler


CANCEL_COMMAND = 'cancel'


@with_db
async def cancel(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    await update.message.reply_text(
        'Ну и ладно, в другой раз тогда'
    )
    return ConversationHandler.END


def get_cancel_handler():
    return CommandHandler(CANCEL_COMMAND, cancel)
