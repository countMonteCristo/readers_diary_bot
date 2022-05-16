from email.message import Message
from enum import unique
import logging
from collections.abc import Iterable

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import (
    ApplicationBuilder, CallbackContext,
    CommandHandler, ConversationHandler, MessageHandler, CallbackQueryHandler,
    filters
)

from db import DB
from entites import User, Review, Author, Story
from utils import reshape
from config import Config


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# TODO: move it to global singleton object?
db = DB(Config.db())
db.prepare()


CONFIRM_POSITIVE = 'Да'
CONFIRM_NEGATIVE = 'Нет'

# ------------------------------------------------------------------------------
# adding new review
TITLE, AUTHOR, REVIEW, RANK, CONFIRM = range(5)

rank_keyboard = [
    [InlineKeyboardButton(str(r*3 + c), callback_data=r*3+c) for c in range(3)] for r in range(2)
]
rank_markup = InlineKeyboardMarkup(rank_keyboard)
# ------------------------------------------------------------------------------


def confirm_pattern(label: str):
    def callable_pattern(data: CallbackQuery.data):
        if isinstance(data, Iterable):
            # if callback data is iterable, it should be in form of
            # answer, {useful_data...}, label
            return data[0] in (CONFIRM_POSITIVE, CONFIRM_NEGATIVE) and data[-1] == label
        else:
            return data in (CONFIRM_POSITIVE, CONFIRM_NEGATIVE)
    return callable_pattern


# Confirm pattern labels
ADD_AUTHOR = 'add_author'
ADD_STORY = 'add_story'

# ENTRY POINT ------------------------------------------------------------------
async def start(update: Update, context: CallbackContext.DEFAULT_TYPE):
    user = User(update.effective_user)
    db.add_user_if_new( user)

    text = '''Привет, {}!
Я - бот для твоего читательского дневника.
Здесь ты можешь отмечать всё, что прочитал, ставить оценки и всякое такое.
    '''.format(user.username)

    await update.message.reply_text(text)
# ------------------------------------------------------------------------------

# ADD AUTHOR -------------------------------------------------------------------
ADD_AUTHOR_CONFIRM = range(1)

async def add_author(update: Update, context: CallbackContext.DEFAULT_TYPE):
    user = User(update.effective_user)
    user_data = context.user_data

    author_name = ' '.join(context.args)
    if author_name:
        author_id = db.author_id(user, author_name)
        if author_id != -1:
            await update.message.reply_text(f'Такой автор уже есть в базе')
            return ConversationHandler.END
        else:
            author: Author = Author(user, name=author_name)
            unique_key = update.effective_message.message_id
            user_data[unique_key] = {
                'author': author
            }
            confirm_reply_keyboard = [
                [InlineKeyboardButton(text, callback_data=(text, unique_key, ADD_AUTHOR),) for text in (CONFIRM_POSITIVE, CONFIRM_NEGATIVE)]
            ]
            confirm_markup = InlineKeyboardMarkup(confirm_reply_keyboard)
            await update.message.reply_text(
                'Добавить автора "{}"?'.format(author.name),
                reply_markup=confirm_markup,
            )
            return ADD_AUTHOR_CONFIRM
    else:
        await update.message.reply_text(f'Добавить автора: `/add_author AUTHOR_NAME`')
        return ConversationHandler.END

async def add_author_name_callback(update: Update, context: CallbackContext.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    answer, unique_id, _ = query.data
    author: Author = context.user_data[unique_id]['author']
    if answer == CONFIRM_POSITIVE:
        db.add_author(author)
        msg = 'добавлен'
    else:
        msg = 'добавление отменено'
    del context.user_data[unique_id]['author']
    await query.edit_message_text(text="{}\nСтатус автора: {}".format(query.message.text, msg))
    return ConversationHandler.END
# ------------------------------------------------------------------------------

# LIST AUTHORS -----------------------------------------------------------------
async def list_authors(update: Update, context: CallbackContext.DEFAULT_TYPE):
    user = User(update.effective_user)
    authors = db.list_authors(user)
    text = 'Твой список авторов:\n\n{}'.format('\n'.join(author.name for author in authors))
    await update.message.reply_text(text)
# ------------------------------------------------------------------------------

# REMOVE AUTHOR ----------------------------------------------------------------
REMOVE_AUTHOR, REMOVE_AUTHOR_CONFIRM = range(2)

async def remove_author(update: Update, context: CallbackContext.DEFAULT_TYPE):
    user = User(update.effective_user)
    authors = db.list_authors(user)
    author_buttons = [
        InlineKeyboardButton(author.name, callback_data=(author.id, author.name)) for author in authors
    ]
    authors_keyboard = reshape(author_buttons, len(authors) // 2 + len(authors) % 2, 2)
    authors_markup = InlineKeyboardMarkup(authors_keyboard)
    await update.message.reply_text('Какого автора ты хочешь удалить?', reply_markup=authors_markup)
    return REMOVE_AUTHOR

# TODO: add cancel button to author buttons list
async def remove_author_callback(update: Update, context: CallbackContext.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    author_id, author_name = query.data

    confirm_reply_keyboard = [
        [InlineKeyboardButton(answer, callback_data=(answer, author_id, author_name)) for answer in (CONFIRM_POSITIVE, CONFIRM_NEGATIVE)]
    ]
    confirm_markup = InlineKeyboardMarkup(confirm_reply_keyboard)

    await query.edit_message_text(
        text=f"Удалить автора `{author_name}`? Вместе с ним удалятся все его произведения, а также все твои записи о них",
        reply_markup=confirm_markup,
    )
    return REMOVE_AUTHOR_CONFIRM

async def remove_author_confirm_callback(update: Update, context: CallbackContext.DEFAULT_TYPE):
    user = User(update.effective_user)
    query = update.callback_query
    await query.answer()

    answer, author_id, author_name = query.data
    if answer == CONFIRM_POSITIVE:
        db.remove_author(user, author_id)
        status_msg = 'удалён'
    else:
        status_msg = 'удаление отменено'

    await query.edit_message_text(text="Статус автора `{}`: {}".format(author_name, status_msg))
    return ConversationHandler.END
# ------------------------------------------------------------------------------


# ADD STORY --------------------------------------------------------------------
ADD_STORY_AUTHOR_CONFIRM, ADD_STORY_CONFIRM = range(2)

async def add_story(update: Update, context: CallbackContext.DEFAULT_TYPE):
    user = User(update.effective_user)
    user_data = context.user_data

    # print('WTF')

    story_title = ' '.join(context.args)
    if story_title:
        # Do not check the uniqueness of the story title, because
        # it is possible for different authors to have same-titled stories
        story: Story = Story(user, title=story_title)
        unique_key = update.effective_message.message_id
        user_data[unique_key] = {
            'story': story
        }
        authors = db.list_authors(user)
        author_buttons = [
            InlineKeyboardButton(author.name, callback_data=(unique_key, author.id, author.name, story.title)) for author in authors
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

async def add_story_author_confirm_callback(update: Update, context: CallbackContext.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    unique_key, author_id, author_name, story_title = query.data
    story: Story = context.user_data[unique_key]['story']
    story.author_name = author_name
    story.author_id = author_id

    confirm_reply_keyboard = [
        [InlineKeyboardButton(answer, callback_data=(answer, unique_key, ADD_STORY)) for answer in (CONFIRM_POSITIVE, CONFIRM_NEGATIVE)]
    ]
    confirm_markup = InlineKeyboardMarkup(confirm_reply_keyboard)

    await query.edit_message_text(
        text=f"Добавить произведение `{story_title}` автора `{author_name}`?",
        reply_markup=confirm_markup,
    )
    return ADD_STORY_CONFIRM

async def add_story_confirm_callback(update: Update, context: CallbackContext.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    answer, unique_key, _ = query.data
    story: Story = context.user_data[unique_key]['story']
    if answer == CONFIRM_POSITIVE:
        db.add_story(story)
        status_msg = 'добавлено'
    else:
        status_msg = 'добавление отменено'
    del context.user_data[unique_key]['story']
    await query.edit_message_text(text="{}\nСтатус произведения: {}".format(query.message.text, status_msg))
    return ConversationHandler.END
# ------------------------------------------------------------------------------

# LIST STORIES -----------------------------------------------------------------
async def list_stories(update: Update, context: CallbackContext.DEFAULT_TYPE):
    user = User(update.effective_user)
    stories = db.list_stories(user)
    text = 'Твой список произведений:\n\n{}'.format('\n'.join(story.title for story in stories))
    await update.message.reply_text(text)
# ------------------------------------------------------------------------------


# REMOVE STORY -----------------------------------------------------------------
# TODO: Возможность выбрать автора перед удалением произведения
REMOVE_STORY_CALLBACK, REMOVE_STORY_CONFIRM = range(2)

async def remove_story(update: Update, context: CallbackContext.DEFAULT_TYPE):
    user = User(update.effective_user)
    stories = db.list_stories(user)
    stories_buttons = [
        InlineKeyboardButton(story.title, callback_data=(story.id, story.title)) for story in stories
    ]
    stories_keyboard = reshape(stories_buttons, len(stories) // 2 + len(stories) % 2, 2)
    stories_markup = InlineKeyboardMarkup(stories_keyboard)
    await update.message.reply_text('Какое произведение ты хочешь удалить?', reply_markup=stories_markup)
    return REMOVE_STORY_CALLBACK

async def remove_story_callback(update: Update, context: CallbackContext.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    story_id, story_title = query.data

    confirm_reply_keyboard = [
        [InlineKeyboardButton(answer, callback_data=(answer, story_id, story_title)) for answer in (CONFIRM_POSITIVE, CONFIRM_NEGATIVE)]
    ]
    confirm_markup = InlineKeyboardMarkup(confirm_reply_keyboard)

    await query.edit_message_text(
        text=f"Удалить произведение `{story_title}`? Вместе с ним удалится твоя запись о нём (если она есть)",
        reply_markup=confirm_markup,
    )
    return REMOVE_STORY_CONFIRM

async def remove_story_confirm_callback(update: Update, context: CallbackContext.DEFAULT_TYPE):
    user = User(update.effective_user)
    query = update.callback_query
    await query.answer()

    answer, story_id, story_title = query.data
    if answer == CONFIRM_POSITIVE:
        db.remove_story(user, story_id)
        status_msg = 'удалено'
    else:
        status_msg = 'удаление отменено'

    await query.edit_message_text(text="Статус произведения `{}`: {}".format(story_title, status_msg))
    return ConversationHandler.END
# ------------------------------------------------------------------------------

"""
async def add_review(update: Update, context: CallbackContext.DEFAULT_TYPE):
    await update.message.reply_text('Давай добавим новую рецензию! Как называется произведение?')
    return TITLE

async def add_review_title(update: Update, context: CallbackContext.DEFAULT_TYPE):
    user = User(update.effective_user)
    user_data = context.user_data
    user_data.clear()
    review = Review(user)
    review.title = update.message.text
    user_data['review'] = review
    await update.message.reply_text('Кто автор "{}"?'.format(review.title))
    return AUTHOR

async def add_review_author(update: Update, context: CallbackContext.DEFAULT_TYPE):
    user_data = context.user_data
    # what if 'review' not in user_data?
    review: Review = user_data['review']
    review.author = update.message.text
    await update.message.reply_text(
        'Aвтор - "{}". Отлично! Какие впечатления у тебя от этого произведения?'.format(review.author)
    )
    return REVIEW

async def add_review_text(update: Update, context: CallbackContext.DEFAULT_TYPE):
    user_data = context.user_data
    # what if 'review' not in user_data?
    review: Review = user_data['review']
    review.text = update.message.text
    await update.message.reply_text(
        'Твоя рецензия: "{}". Какую оценку поставишь?'.format(review.text),
        reply_markup=rank_markup
    )
    # return RANK

async def add_review_rank_callback(update: Update, context: CallbackContext.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    print(query.message)
    await query.edit_message_text(text="{}\nТвоя оценка: {query.data}".format(query.message.text, query.data))
    return RANK

async def add_review_rank(update: Update, context: CallbackContext.DEFAULT_TYPE):
    user_data = context.user_data
    # what if 'review' not in user_data?
    review: Review = user_data['review']
    review.rank = int(update.message.text)
    text = f'''Давай проверим, всё ли верно:
Произведение: "{review.title}"
Автор: "{review.author}"
Рецензия: "{review.text}"
Оценка: {review.rank}
    '''
    await update.message.reply_text(text, reply_markup=confirm_markup)
    return CONFIRM

async def add_review_confirm(update: Update, context: CallbackContext.DEFAULT_TYPE):
    review: Review = context.user_data['review']
    if update.message.text == 'Сохранить':
        db.save_review(review)
        text = 'Рецензия сохранена!'
    else:
        context.user_data.clear()
        text = 'Добавление рецензии отменено'
    await update.message.reply_text(
        text, reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END
"""

async def cancel(update: Update, context: CallbackContext.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ну и ладно, в другой раз тогда"
    )
    return ConversationHandler.END


if __name__ == '__main__':
    application = ApplicationBuilder().token(Config.token()).arbitrary_callback_data(True).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    add_author_handler = ConversationHandler(
        entry_points=[CommandHandler(ADD_AUTHOR, add_author, filters=~filters.UpdateType.EDITED_MESSAGE)],
        states={
            ADD_AUTHOR_CONFIRM: [CallbackQueryHandler(add_author_name_callback, pattern=confirm_pattern(ADD_AUTHOR))],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(add_author_handler)

    application.add_handler(CommandHandler('list_authors', list_authors, filters=~filters.UpdateType.EDITED_MESSAGE))

    remove_author_handler = ConversationHandler(
        entry_points=[CommandHandler("remove_author", remove_author, filters=~filters.UpdateType.EDITED_MESSAGE)],
        states={
            REMOVE_AUTHOR: [CallbackQueryHandler(remove_author_callback)],
            REMOVE_AUTHOR_CONFIRM: [CallbackQueryHandler(remove_author_confirm_callback)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(remove_author_handler)

    add_story_handler = ConversationHandler(
        entry_points=[CommandHandler(ADD_STORY, add_story, filters=~filters.UpdateType.EDITED_MESSAGE)],
        states={
            ADD_STORY_AUTHOR_CONFIRM: [CallbackQueryHandler(add_story_author_confirm_callback)],
            ADD_STORY_CONFIRM: [CallbackQueryHandler(add_story_confirm_callback, pattern=confirm_pattern(ADD_STORY))],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(add_story_handler)

    application.add_handler(CommandHandler('list_stories', list_stories, filters=~filters.UpdateType.EDITED_MESSAGE))

    remove_story_handler = ConversationHandler(
        entry_points=[CommandHandler("remove_story", remove_story, filters=~filters.UpdateType.EDITED_MESSAGE)],
        states={
            REMOVE_STORY_CALLBACK: [CallbackQueryHandler(remove_story_callback)],
            REMOVE_STORY_CONFIRM: [CallbackQueryHandler(remove_story_confirm_callback)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(remove_story_handler)

    # conv_handler = ConversationHandler(
    #     entry_points=[CommandHandler("add_review", add_review)],
    #     states={
    #         TITLE: [MessageHandler(filters.TEXT, add_review_title)],
    #         AUTHOR: [MessageHandler(filters.TEXT, add_review_author)],
    #         REVIEW: [MessageHandler(filters.TEXT, add_review_text)],
    #         RANK: [MessageHandler(filters.TEXT, add_review_rank)],
    #         CONFIRM: [MessageHandler(filters.TEXT, add_review_confirm)]
    #     },
    #     fallbacks=[CommandHandler("cancel", cancel)],
    # )
    # application.add_handler(conv_handler)
    # application.add_handler(CallbackQueryHandler(add_review_rank_callback))

    application.run_polling()
