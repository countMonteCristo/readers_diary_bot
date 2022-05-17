from itertools import groupby
import logging

from consts import CONFIRM_POSITIVE
from db import DB
from entites import Author, Story, User
from keyboards.author import authors_inline_keyboard
from keyboards.story import stories_inline_keyboard
from keyboards.confirm import confirm_inline_keyboard
from utils import update_confirm_status, with_db

from telegram import Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler, CommandHandler, ConversationHandler, filters
)


ADD_STORY = 'add_story'
LIST_STORIES = 'list_stories'
REMOVE_STORY = 'remove_story'


# ADD STORY ------------------------------------------------------------------------------------------------------------
ADD_STORY_AUTHOR_CONFIRM, ADD_STORY_CONFIRM = range(2)


@with_db
async def add_story(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    if update.message is None:
        return ConversationHandler.END
    if not context.args:
        await update.message.reply_text(f'Добавить произведение: `/add_story STORY_TITLE`')
        return ConversationHandler.END

    story_title = ' '.join(context.args)
    # Do not check the uniqueness of the story title, because
    # it is possible for different authors to have same-titled stories
    story = Story(user, title=story_title)

    authors = db.list_authors(user)
    author_markup = authors_inline_keyboard(authors, optional_data=(story,))
    await update.message.reply_text(
        'Кто автор произведения `{}`?'.format(story.title),
        reply_markup=author_markup,
    )
    return ADD_STORY_AUTHOR_CONFIRM


# TODO: check uniqueness of the story title for specified author
@with_db
async def add_story_author_confirm_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await query.answer()

    if query.data is None:
        logging.error('query.data is None in add_story_author_confirm_callback()')
        return ConversationHandler.END

    story: Story
    author: Author

    author, story = query.data      # type: ignore
    story.author_name = author.name
    story.author_id = author.id

    confirm_markup = confirm_inline_keyboard(optional_data=(story,))

    await query.edit_message_text(
        text=f"Добавить произведение `{story.title}` автора `{author.name}`?",
        reply_markup=confirm_markup,
    )
    return ADD_STORY_CONFIRM


@with_db
async def add_story_confirm_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await query.answer()

    if query.message is None:
        logging.error('query.message is None in add_story_confirm_callback()')
        return ConversationHandler.END

    if query.data is None:
        logging.error('query.data is None in add_story_confirm_callback')
        return ConversationHandler.END

    answer: str
    story: Story
    answer, story = query.data      # type: ignore
    if answer == CONFIRM_POSITIVE:
        db.add_story(story)
        status_msg = 'добавлено'
    else:
        status_msg = 'добавление отменено'
    await update_confirm_status(query, status_msg)
    return ConversationHandler.END
# ----------------------------------------------------------------------------------------------------------------------

# LIST STORIES ---------------------------------------------------------------------------------------------------------
@with_db
async def list_stories(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    if update.message is None:
        return ConversationHandler.END

    stories = db.list_stories(user)
    stories_list = []
    for key, author_stories in groupby(stories, key=lambda story: story.author_name):
        author_story_lits = '{}:\n{}'.format(key, '\n'.join('    {}'.format(story.title) for story in author_stories))
        stories_list.append(author_story_lits)
    text = 'Твой список произведений:\n\n{}'.format('\n\n'.join(stories_list))
    await update.message.reply_text(text)
# ----------------------------------------------------------------------------------------------------------------------


# REMOVE STORY ---------------------------------------------------------------------------------------------------------
# TODO: Возможность выбрать автора перед удалением произведения
REMOVE_STORY_CALLBACK, REMOVE_STORY_CONFIRM = range(2)


@with_db
async def remove_story(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    if update.message is None:
        return ConversationHandler.END

    stories = db.list_stories(user)
    story_markup = stories_inline_keyboard(stories)

    await update.message.reply_text('Какое произведение ты хочешь удалить?', reply_markup=story_markup)
    return REMOVE_STORY_CALLBACK


@with_db
async def remove_story_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await query.answer()

    if query.data is None:
        logging.error('query.data is None in remove_story_callback()')
        return ConversationHandler.END

    story: Story
    story, = query.data     # type: ignore

    confirm_markup = confirm_inline_keyboard(optional_data=(story,))

    await query.edit_message_text(
        text=f"Удалить произведение `{story.title}`? Вместе с ним удалится твоя запись о нём (если она есть)",
        reply_markup=confirm_markup,
    )
    return REMOVE_STORY_CONFIRM


@with_db
async def remove_story_confirm_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await query.answer()

    if query.message is None:
        logging.error('query.message is None in remove_story_confirm_callback()')
        return ConversationHandler.END

    if query.data is None:
        logging.error('query.data is None in remove_story_confirm_callback')
        return ConversationHandler.END

    answer: str
    story: Story
    answer, story = query.data      # type: ignore

    if answer == CONFIRM_POSITIVE:
        db.remove_story(user, story.id)
        status_msg = 'удалено'
    else:
        status_msg = 'удаление отменено'

    await update_confirm_status(query, status_msg)
    return ConversationHandler.END
# ----------------------------------------------------------------------------------------------------------------------


def get_story_handlers(cancel_handler: CommandHandler):
    add_story_handler = ConversationHandler(
        entry_points=[CommandHandler(ADD_STORY, add_story, filters=~filters.UpdateType.EDITED_MESSAGE)],
        states={
            ADD_STORY_AUTHOR_CONFIRM: [CallbackQueryHandler(add_story_author_confirm_callback)],
            ADD_STORY_CONFIRM: [CallbackQueryHandler(add_story_confirm_callback)],
        },
        fallbacks=[cancel_handler],
    )

    list_stories_handler = CommandHandler(LIST_STORIES, list_stories, filters=~filters.UpdateType.EDITED_MESSAGE)

    remove_story_handler = ConversationHandler(
        entry_points=[CommandHandler(REMOVE_STORY, remove_story, filters=~filters.UpdateType.EDITED_MESSAGE)],
        states={
            REMOVE_STORY_CALLBACK: [CallbackQueryHandler(remove_story_callback)],
            REMOVE_STORY_CONFIRM: [CallbackQueryHandler(remove_story_confirm_callback)],
        },
        fallbacks=[cancel_handler],
    )

    return (
        add_story_handler, list_stories_handler, remove_story_handler
    )
