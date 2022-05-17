from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler, CommandHandler, ConversationHandler, filters
)

from consts import CONFIRM_ANSWERS, CONFIRM_POSITIVE
from db import DB
from entites import Author, User
from utils import reshape, update_confirm_status, with_db


ADD_AUTHOR = 'add_author'
LIST_AUTHORS = 'list_authors'
REMOVE_AUTHOR = 'remove_author'


# ADD AUTHOR -----------------------------------------------------------------------------------------------------------
ADD_AUTHOR_CONFIRM = 0


@with_db
async def add_author(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):

    author_name = ' '.join(context.args)
    if author_name:
        author_id = db.author_id(user, author_name)
        if author_id != -1:
            await update.message.reply_text(f'Такой автор уже есть в базе')
            return ConversationHandler.END
        else:
            author = Author(user, name=author_name)
            confirm_reply_keyboard = [
                [InlineKeyboardButton(text, callback_data=(text, author)) for text in CONFIRM_ANSWERS]
            ]
            confirm_markup = InlineKeyboardMarkup(confirm_reply_keyboard)
            await update.message.reply_text('Добавить автора "{}"?'.format(author.name), reply_markup=confirm_markup)
            return ADD_AUTHOR_CONFIRM
    else:
        await update.message.reply_text(f'Добавить автора: `/add_author AUTHOR_NAME`')
        return ConversationHandler.END


@with_db
async def add_author_name_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    await query.answer()

    answer, author = query.data

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
    authors = db.list_authors(user)
    text = 'Твой список авторов:\n\n{}'.format('\n'.join(author.name for author in authors))
    await update.message.reply_text(text)
# ----------------------------------------------------------------------------------------------------------------------

# REMOVE AUTHOR --------------------------------------------------------------------------------------------------------
REMOVE_AUTHOR_ACTION, REMOVE_AUTHOR_CONFIRM = range(2)


@with_db
async def remove_author(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    authors = db.list_authors(user)
    author_buttons = [
        InlineKeyboardButton(author.name, callback_data=author) for author in authors
    ]
    authors_keyboard = reshape(author_buttons, len(authors) // 2 + len(authors) % 2, 2)
    authors_markup = InlineKeyboardMarkup(authors_keyboard)
    await update.message.reply_text('Какого автора ты хочешь удалить?', reply_markup=authors_markup)
    return REMOVE_AUTHOR_ACTION

# TODO: add cancel button to author buttons list
@with_db
async def remove_author_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    await query.answer()

    author: Author = query.data

    confirm_reply_keyboard = [
        [InlineKeyboardButton(answer, callback_data=(answer, author)) for answer in CONFIRM_ANSWERS]
    ]
    confirm_markup = InlineKeyboardMarkup(confirm_reply_keyboard)

    text = f"Удалить автора `{author.name}`? Вместе с ним удалятся все его произведения, а также все твои записи о них"
    await query.edit_message_text(text=text, reply_markup=confirm_markup)
    return REMOVE_AUTHOR_CONFIRM


@with_db
async def remove_author_confirm_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    await query.answer()

    answer: str
    author: Author
    answer, author = query.data
    if answer == CONFIRM_POSITIVE:
        db.remove_author(user, author.id)
        status_msg = 'удалён'
    else:
        status_msg = 'удаление отменено'

    await update_confirm_status(query, status_msg)
    return ConversationHandler.END
# ----------------------------------------------------------------------------------------------------------------------


def get_author_handlers(cancel_handler: CommandHandler):
    add_author_handler = ConversationHandler(
        entry_points=[CommandHandler(ADD_AUTHOR, add_author, filters=~filters.UpdateType.EDITED_MESSAGE)],
        states={
            ADD_AUTHOR_CONFIRM: [CallbackQueryHandler(add_author_name_callback)],
        },
        fallbacks=[cancel_handler],
    )

    list_authors_handler = CommandHandler(LIST_AUTHORS, list_authors, filters=~filters.UpdateType.EDITED_MESSAGE)

    remove_author_handler = ConversationHandler(
        entry_points=[CommandHandler(REMOVE_AUTHOR, remove_author, filters=~filters.UpdateType.EDITED_MESSAGE)],
        states={
            REMOVE_AUTHOR_ACTION: [CallbackQueryHandler(remove_author_callback)],
            REMOVE_AUTHOR_CONFIRM: [CallbackQueryHandler(remove_author_confirm_callback)],
        },
        fallbacks=[cancel_handler],
    )

    return (
        add_author_handler, list_authors_handler, remove_author_handler
    )
