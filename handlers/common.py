from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, ConversationHandler, CallbackQueryHandler

from db import DB
from entites import User
from utils import with_db, update_confirm_status


CANCEL_COMMAND = 'cancel'


@with_db
async def fallback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    if update.message is None:
        return ConversationHandler.END

    await update.message.reply_text(
        'Ну и ладно, в другой раз тогда'
    )
    return ConversationHandler.END


def get_fallback_handler():
    return CommandHandler(CANCEL_COMMAND, fallback)


@with_db
async def cancel(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await update_confirm_status(query, 'отмена')
    return ConversationHandler.END


def get_cancel_handler():
    return CallbackQueryHandler(cancel)
