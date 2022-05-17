import logging

from telegram import Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler, CommandHandler, ConversationHandler, filters
)

from consts import CONFIRM_POSITIVE
from db import DB, INVALID_ID
from entities import Author, User
from formatters import format_authors
from keyboards import authors_inline_keyboard, confirm_inline_keyboard
from utils import update_confirm_status, with_db


ADD_AUTHOR = 'add_author'
LIST_AUTHORS = 'list_authors'
REMOVE_AUTHOR = 'remove_author'


# ADD AUTHOR -----------------------------------------------------------------------------------------------------------
ADD_AUTHOR_CONFIRM, = range(1)


@with_db
async def add_author(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    if update.message is None:
        return ConversationHandler.END
    if not context.args:
        await update.message.reply_text(f'Добавить автора: `/add_author AUTHOR_NAME`')
        return ConversationHandler.END

    author_name = ' '.join(context.args)
    author_id = db.author_id(user, author_name)
    if author_id != INVALID_ID:
        await update.message.reply_text(f'Такой автор уже есть в базе')
        return ConversationHandler.END
    else:
        author = Author(user, name=author_name)
        confirm_markup = confirm_inline_keyboard(optional_data=(author,))
        await update.message.reply_text('Добавить автора `{}`?'.format(author.name), reply_markup=confirm_markup)
        return ADD_AUTHOR_CONFIRM


@with_db
async def add_author_name_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await query.answer()

    if query.message is None:
        logging.error('query.message is None')
        return ConversationHandler.END

    if query.data is None:
        logging.error('query.data is None in add_author_name_callback()')
        return ConversationHandler.END
    answer: str
    author: Author
    answer, author = query.data     # type: ignore

    if answer == CONFIRM_POSITIVE:
        db.add_author(author)
        status_msg = 'добавлен'
    else:
        status_msg = 'добавление отменено'
    await update_confirm_status(query, status_msg)

    return ConversationHandler.END
# ----------------------------------------------------------------------------------------------------------------------


# LIST AUTHORS ---------------------------------------------------------------------------------------------------------
@with_db
async def list_authors(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    if update.message is None:
        return ConversationHandler.END

    authors = db.list_authors(user)
    authors_str = format_authors(authors)
    text = f'Твой список авторов:\n\n{authors_str}'

    await update.message.reply_text(text)
# ----------------------------------------------------------------------------------------------------------------------

# REMOVE AUTHOR --------------------------------------------------------------------------------------------------------
REMOVE_AUTHOR_ACTION, REMOVE_AUTHOR_CONFIRM = range(2)


@with_db
async def remove_author(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    if update.message is None:
        return ConversationHandler.END

    authors = db.list_authors(user)
    author_markup = authors_inline_keyboard(authors)
    await update.message.reply_text('Какого автора ты хочешь удалить?', reply_markup=author_markup)
    return REMOVE_AUTHOR_ACTION


@with_db
async def remove_author_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await query.answer()

    if query.data is None:
        logging.error('query.data is None in remove_author_callback()')
        return ConversationHandler.END

    author: Author
    author, = query.data    # type: ignore
    confirm_markup = confirm_inline_keyboard(optional_data=(author,))

    text = f'Удалить автора `{author.name}`? Вместе с ним удалятся все его произведения, а также все твои записи о них'
    await query.edit_message_text(text=text, reply_markup=confirm_markup)
    return REMOVE_AUTHOR_CONFIRM


@with_db
async def remove_author_confirm_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await query.answer()

    if query.message is None:
        logging.error('query.message is None')
        return ConversationHandler.END

    if query.data is None:
        logging.error('query.data is None in remove_author_confirm_callback()')
        return ConversationHandler.END

    answer: str
    author: Author
    answer, author = query.data     # type: ignore
    if answer == CONFIRM_POSITIVE:
        db.remove_author(user, author.id)
        status_msg = 'удалён'
    else:
        status_msg = 'удаление отменено'

    await update_confirm_status(query, status_msg)
    return ConversationHandler.END
# ----------------------------------------------------------------------------------------------------------------------


def get_author_handlers(fallback_handler: CommandHandler, cancel_handler: CallbackQueryHandler):
    add_author_handler = ConversationHandler(
        entry_points=[CommandHandler(ADD_AUTHOR, add_author, filters=~filters.UpdateType.EDITED_MESSAGE)],
        states={
            ADD_AUTHOR_CONFIRM: [CallbackQueryHandler(add_author_name_callback)],
        },
        fallbacks=[fallback_handler],
    )

    list_authors_handler = CommandHandler(LIST_AUTHORS, list_authors, filters=~filters.UpdateType.EDITED_MESSAGE)

    remove_author_handler = ConversationHandler(
        entry_points=[CommandHandler(REMOVE_AUTHOR, remove_author, filters=~filters.UpdateType.EDITED_MESSAGE)],
        states={
            REMOVE_AUTHOR_ACTION: [
                CallbackQueryHandler(remove_author_callback, pattern=tuple),
                cancel_handler,
            ],
            REMOVE_AUTHOR_CONFIRM: [CallbackQueryHandler(remove_author_confirm_callback)],
        },
        fallbacks=[fallback_handler],
    )

    return (
        add_author_handler, list_authors_handler, remove_author_handler
    )
