from db import DB
from utils import with_db, reshape, update_confirm_status
from consts import CONFIRM_POSITIVE, CONFIRM_ANSWERS
from entites import User, Story, Author

from .common import get_cancel_handler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext,
    ConversationHandler, CommandHandler, CallbackQueryHandler,
    filters
)

from itertools import groupby


ADD_STORY = 'add_story'
LIST_STORIES = 'list_stories'
REMOVE_STORY = 'remove_story'


# ADD STORY ------------------------------------------------------------------------------------------------------------
ADD_STORY_AUTHOR_CONFIRM, ADD_STORY_CONFIRM = range(2)


@with_db
async def add_story(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    story_title = ' '.join(context.args)
    if story_title:
        # Do not check the uniqueness of the story title, because
        # it is possible for different authors to have same-titled stories
        story = Story(user, title=story_title)
        authors = db.list_authors(user)
        author_buttons = [
            InlineKeyboardButton(author.name, callback_data=(story, author)) for author in authors
        ]
        authors_keyboard = reshape(author_buttons, len(authors) // 2 + len(authors) % 2, 2)
        authors_markup = InlineKeyboardMarkup(authors_keyboard)
        await update.message.reply_text(
            'Кто автор произведения `{}`?'.format(story.title),
            reply_markup=authors_markup,
        )
        return ADD_STORY_AUTHOR_CONFIRM
    else:
        await update.message.reply_text(f'Добавить произведение: `/add_story STORY_TITLE`')
        return ConversationHandler.END


@with_db
async def add_story_author_confirm_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    await query.answer()

    story: Story
    author: Author

    story, author = query.data
    story.author_name = author.name
    story.author_id = author.id

    confirm_reply_keyboard = [
        [InlineKeyboardButton(answer, callback_data=(answer, story)) for answer in CONFIRM_ANSWERS]
    ]
    confirm_markup = InlineKeyboardMarkup(confirm_reply_keyboard)

    await query.edit_message_text(
        text=f"Добавить произведение `{story.title}` автора `{author.name}`?",
        reply_markup=confirm_markup,
    )
    return ADD_STORY_CONFIRM


@with_db
async def add_story_confirm_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    await query.answer()

    answer: str
    story: Story
    answer, story = query.data
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
    stories = groupby(db.list_stories(user), key=lambda story: story.author_name)
    stories_list = []
    for key, author_stories in stories:
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
    stories = db.list_stories(user)
    stories_buttons = [
        InlineKeyboardButton(story.title, callback_data=story) for story in stories
    ]
    stories_keyboard = reshape(stories_buttons, len(stories) // 2 + len(stories) % 2, 2)
    stories_markup = InlineKeyboardMarkup(stories_keyboard)
    await update.message.reply_text('Какое произведение ты хочешь удалить?', reply_markup=stories_markup)
    return REMOVE_STORY_CALLBACK


@with_db
async def remove_story_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    await query.answer()

    story: Story = query.data

    confirm_reply_keyboard = [
        [InlineKeyboardButton(answer, callback_data=(answer, story)) for answer in CONFIRM_ANSWERS]
    ]
    confirm_markup = InlineKeyboardMarkup(confirm_reply_keyboard)

    await query.edit_message_text(
        text=f"Удалить произведение `{story.title}`? Вместе с ним удалится твоя запись о нём (если она есть)",
        reply_markup=confirm_markup,
    )
    return REMOVE_STORY_CONFIRM


@with_db
async def remove_story_confirm_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    await query.answer()

    answer: str
    story: Story
    answer, story = query.data

    if answer == CONFIRM_POSITIVE:
        db.remove_story(user, story.id)
        status_msg = 'удалено'
    else:
        status_msg = 'удаление отменено'

    await update_confirm_status(query, status_msg)
    return ConversationHandler.END
# ----------------------------------------------------------------------------------------------------------------------


def get_story_handlers():
    cancel_handler = get_cancel_handler()

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
