from itertools import groupby
import logging

from consts import CONFIRM_POSITIVE
from db import DB
from entites import Author, Review, Story, User
from keyboards.author import authors_inline_keyboard
from keyboards.story import stories_inline_keyboard
from keyboards.confirm import confirm_inline_keyboard
from utils import reshape, update_confirm_status, with_db

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext, CallbackQueryHandler, CommandHandler, ConversationHandler, filters
)


ADD_REVIEW = 'add_review'
LIST_REVIEWS = 'list_reviews'
REMOVE_REVIEW = 'remove_review'


# ADD REVIEW -----------------------------------------------------------------------------------------------------------
ADD_REVIEW_STORY, ADD_REVIEW_RANK, ADD_REVIEW_CONFIRM, ADD_REVIEW_CONFIRM_CALLBACK = range(4)


@with_db
async def add_review(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    if update.message is None:
        return ConversationHandler.END
    if not context.args:
        await update.message.reply_text(f'Добавить отзыв: `/add_review REVIEW_TEXT`')
        return ConversationHandler.END

    review_text = ' '.join(context.args)
    review = Review(user, text=review_text)

    authors = db.list_authors(user)
    author_markup = authors_inline_keyboard(authors, optional_data=(review,))

    await update.message.reply_text(
        'Выбери автора', reply_markup=author_markup,
    )
    return ADD_REVIEW_STORY


@with_db
async def add_review_story_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await query.answer()

    if query.data is None:
        logging.error('query.data is None in add_review_story_callback()')
        return ConversationHandler.END

    author: Author
    review: Review
    author, review = query.data     # type: ignore

    review.author_name = author.name
    review.author_id = author.id

    stories = db.list_stories(user, author_id=author.id)
    story_markup = stories_inline_keyboard(stories, optional_data=(review,))

    await query.edit_message_text(
        text=f"Выбери произведение автора `{author.name}`",
        reply_markup=story_markup,
    )
    return ADD_REVIEW_RANK


@with_db
async def add_review_rank(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await query.answer()

    if query.data is None:
        logging.error('query.data is None in add_review_rank()')
        return ConversationHandler.END

    story: Story
    review: Review
    story, review = query.data      # type: ignore

    review.story_id = story.id
    review.story_title = story.title

    rank_buttons = [InlineKeyboardButton(str(rank), callback_data=(review, rank)) for rank in range(6)]
    rank_keyborad = reshape(rank_buttons, 2, 3)
    rank_markup = InlineKeyboardMarkup(rank_keyborad)

    await query.edit_message_text(
        text=f"Оцени произведение `{review.story_title}` автора `{review.author_name}`",
        reply_markup=rank_markup,
    )
    return ADD_REVIEW_CONFIRM


@with_db
async def add_review_confirm(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await query.answer()

    if query.data is None:
        logging.error('query.data is None in add_review_confirm()')
        return ConversationHandler.END

    review: Review
    rank: int
    review, rank = query.data       # type: ignore
    review.rank = rank

    confirm_markup = confirm_inline_keyboard(optional_data=(review,))

    text = 'Добавить отзыв на произведение `{}` автора `{}` с оценкой `{}`?'.format(
        review.story_title, review.author_name, review.rank
    )
    await query.edit_message_text(text=text, reply_markup=confirm_markup)
    return ADD_REVIEW_CONFIRM_CALLBACK


@with_db
async def add_review_confirm_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await query.answer()

    if query.message is None:
        logging.error('query.message is None in add_review_confirm_callback()')
        return ConversationHandler.END

    if query.data is None:
        logging.error('query.data is None in add_review_confirm_callback()')
        return ConversationHandler.END

    answer: str
    review: Review
    answer, review = query.data     # type: ignore

    if answer == CONFIRM_POSITIVE:
        db.add_review(review)
        status_msg = 'добавлен'
    else:
        status_msg = 'добавление отменено'

    await update_confirm_status(query, status_msg)
    return ConversationHandler.END
# ----------------------------------------------------------------------------------------------------------------------


# LIST REVIEWS ---------------------------------------------------------------------------------------------------------
@with_db
async def list_reviews(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    if update.message is None:
        return ConversationHandler.END

    # TODO: add formatter functions for list_* commands
    author_sep = '-' * 50
    reviews_plain = db.list_reviews(user)
    reviews_list = []
    for author_key, author_reviews in groupby(reviews_plain, key=lambda r: r.author_name):
        author_review_list = []
        for story_key, author_story_reviews_group in groupby(author_reviews, key=lambda r: r.story_title):
            rec = '  "{}":\n{}'.format(
                story_key, '\n'.join('    - [{}] {}'.format(r.rank, r.text) for r in author_story_reviews_group)
            )
            author_review_list.append(rec)
        author_rec = '{}:\n{}\n'.format(author_key, ' \n\n'.join(author_review_list))
        reviews_list.append(author_rec)

    text = 'Твой список отзывов:\n\n{}'.format(f'{author_sep}\n'.join(reviews_list))
    await update.message.reply_text(text)
# ----------------------------------------------------------------------------------------------------------------------


# REMOVE REVIEW --------------------------------------------------------------------------------------------------------
REMOVE_REVIEW_GET_STORY, REMOVE_REVIEW_GET_REVIEW, REMOVE_REVIEW_CONFIRM, REMOVE_REVIEW_CONFIRM_CALLBACK = range(4)


@with_db
async def remove_review(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    if update.message is None:
        return ConversationHandler.END

    authors = db.list_authors(user)
    author_markup = authors_inline_keyboard(authors)

    await update.message.reply_text('Выбери автора', reply_markup=author_markup)
    return REMOVE_REVIEW_GET_STORY


@with_db
async def remove_review_get_story(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await query.answer()

    if query.data is None:
        logging.error('query.data is None in remove_review_get_story()')
        return ConversationHandler.END

    author: Author
    author, = query.data    # type: ignore

    stories = db.list_stories(user, author.id)
    story_markup = stories_inline_keyboard(stories, optional_data=(author,))

    await query.edit_message_text(
        text=f'Выбери произведение автора {author.name}',
        reply_markup=story_markup,
    )
    return REMOVE_REVIEW_GET_REVIEW


@with_db
async def remove_review_get_review(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await query.answer()

    if query.data is None:
        logging.error('query.data is None in remove_review_get_review()')
        return ConversationHandler.END

    author: Author
    story: Story
    story, author = query.data      # type: ignore

    reviews = db.list_story_reviews(user, story_id=story.id)
    reviews_buttons = [
        InlineKeyboardButton(review.text[:15], callback_data=(author, story, review)) for review in reviews
    ]
    reviews_keyboard = reshape(reviews_buttons, len(reviews) // 2 + len(reviews) % 2, 2)
    reviews_markup = InlineKeyboardMarkup(reviews_keyboard)

    await query.edit_message_text(
        text=f'Выбери свой отзыв на произведение `{story.title}` автора `{author.name}`',
        reply_markup=reviews_markup,
    )
    return REMOVE_REVIEW_CONFIRM


@with_db
async def remove_review_confirm(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await query.answer()

    if query.data is None:
        logging.error('query.data is None in remove_review_confirm()')
        return ConversationHandler.END

    author: Author
    story: Story
    review: Review
    author, story, review = query.data      # type: ignore

    confirm_markup = confirm_inline_keyboard(optional_data=(review,))

    await query.edit_message_text(
        text=f"Удалить отзыв на произведение `{story.title}` автора `{author.name}`?",
        reply_markup=confirm_markup,
    )
    return REMOVE_REVIEW_CONFIRM_CALLBACK


@with_db
async def remove_review_confirm_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await query.answer()

    if query.message is None:
        logging.error('query.message is None in remove_review_confirm_callback()')
        return ConversationHandler.END

    if query.data is None:
        logging.error('query.data is None in remove_review_confirm_callback()')
        return ConversationHandler.END

    answer: str
    review: Review
    answer, review = query.data     # type: ignore
    if answer == CONFIRM_POSITIVE:
        db.remove_review(user, review.id)
        status_msg = 'удалён'
    else:
        status_msg = 'удаление отменено'

    await update_confirm_status(query, status_msg)
    return ConversationHandler.END
# ----------------------------------------------------------------------------------------------------------------------


def get_review_handlers(cancel_handler: CommandHandler):
    add_review_handler = ConversationHandler(
        entry_points=[CommandHandler(ADD_REVIEW, add_review, filters=~filters.UpdateType.EDITED_MESSAGE)],
        states={
            ADD_REVIEW_STORY: [CallbackQueryHandler(add_review_story_callback)],
            ADD_REVIEW_RANK: [CallbackQueryHandler(add_review_rank)],
            ADD_REVIEW_CONFIRM: [CallbackQueryHandler(add_review_confirm)],
            ADD_REVIEW_CONFIRM_CALLBACK: [
                CallbackQueryHandler(add_review_confirm_callback)
            ],
        },
        fallbacks=[cancel_handler],
    )

    list_reviews_handler = CommandHandler(LIST_REVIEWS, list_reviews, filters=~filters.UpdateType.EDITED_MESSAGE)

    remove_review_handler = ConversationHandler(
        entry_points=[CommandHandler(REMOVE_REVIEW, remove_review, filters=~filters.UpdateType.EDITED_MESSAGE)],
        states={
            REMOVE_REVIEW_GET_STORY: [CallbackQueryHandler(remove_review_get_story)],
            REMOVE_REVIEW_GET_REVIEW: [CallbackQueryHandler(remove_review_get_review)],
            REMOVE_REVIEW_CONFIRM: [CallbackQueryHandler(remove_review_confirm)],
            REMOVE_REVIEW_CONFIRM_CALLBACK: [CallbackQueryHandler(remove_review_confirm_callback)],
        },
        fallbacks=[cancel_handler],
    )

    return [
        add_review_handler, list_reviews_handler, remove_review_handler
    ]
