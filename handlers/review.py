from utils import with_db, reshape, confirm_pattern
from db import DB
from entites import User, Review
from .common import get_cancel_handler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext,
    ConversationHandler, CommandHandler, CallbackQueryHandler,
    filters
)

from consts import CONFIRM_POSITIVE, CONFIRM_ANSWERS
from utils import update_confirm_status


ADD_REVIEW = 'add_review'
LIST_REVIEWS = 'list_reviews'
REMOVE_REVIEW = 'remove_review'


# ADD REVIEW -----------------------------------------------------------------------------------------------------------
ADD_REVIEW_STORY, ADD_REVIEW_RANK, ADD_REVIEW_CONFIRM, ADD_REVIEW_CONFIRM_CALLBACK = range(4)


@with_db
async def add_review(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    user_data = context.user_data

    review_text = ' '.join(context.args)
    if review_text:
        review = Review(user, text=review_text)
        unique_key = update.effective_message.message_id
        user_data[unique_key] = {
            'review': review
        }
        authors = db.list_authors(user)
        author_buttons = [
            InlineKeyboardButton(
                author.name, callback_data=(unique_key, author.id, author.name)
            ) for author in authors
        ]
        authors_keyboard = reshape(author_buttons, len(authors) // 2 + len(authors) % 2, 2)
        authors_markup = InlineKeyboardMarkup(authors_keyboard)
        await update.message.reply_text(
            'Выбери автора', reply_markup=authors_markup,
        )
        return ADD_REVIEW_STORY
    else:
        await update.message.reply_text(f'Добавить отзыв: `/add_review REVIEW_TEXT`')
        return ConversationHandler.END


@with_db
async def add_review_story_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    await query.answer()

    unique_key, author_id, author_name = query.data
    review: Review = context.user_data[unique_key]['review']
    review.author_name = author_name
    review.author_id = author_id

    stories = db.list_stories(user, author_id=author_id)
    story_buttons = [
        InlineKeyboardButton(
            story.title, callback_data=(unique_key, story.id, story.title)
        ) for story in stories
    ]
    stories_keyboard = reshape(story_buttons, len(stories) // 2 + len(stories) % 2, 2)
    stories_markup = InlineKeyboardMarkup(stories_keyboard)

    await query.edit_message_text(
        text=f"Выбери произведение автора `{author_name}`",
        reply_markup=stories_markup,
    )
    return ADD_REVIEW_RANK


@with_db
async def add_review_rank(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    await query.answer()

    unique_key, story_id, story_title = query.data
    review: Review = context.user_data[unique_key]['review']
    review.story_id = story_id
    review.story_title = story_title

    rank_buttons = [InlineKeyboardButton(str(rank), callback_data=(unique_key, rank)) for rank in range(6)]
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
    await query.answer()

    unique_key, rank = query.data
    review: Review = context.user_data[unique_key]['review']
    review.rank = rank

    confirm_reply_keyboard = [
        [InlineKeyboardButton(answer, callback_data=(answer, unique_key, ADD_REVIEW)) for answer in CONFIRM_ANSWERS]
    ]
    confirm_markup = InlineKeyboardMarkup(confirm_reply_keyboard)

    text = 'Добавить отзыв на произведение `{}` автора `{}` с оценкой `{}`?'.format(
        review.story_title, review.author_name, review.rank
    )
    await query.edit_message_text(text=text, reply_markup=confirm_markup)
    return ADD_REVIEW_CONFIRM_CALLBACK


@with_db
async def add_review_confirm_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    await query.answer()

    answer, unique_key, _ = query.data
    review: Review = context.user_data[unique_key]['review']
    if answer == CONFIRM_POSITIVE:
        db.add_review(review)
        status_msg = 'добавлен'
    else:
        status_msg = 'добавление отменено'
    del context.user_data[unique_key]['review']
    await update_confirm_status(query, status_msg)
    return ConversationHandler.END
# ----------------------------------------------------------------------------------------------------------------------


# LIST REVIEWS ---------------------------------------------------------------------------------------------------------
@with_db
async def list_reviews(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    # TODO: group reviews by author and story
    reviews = db.list_reviews(user)
    text = 'Твой список отзывов:\n\n{}'.format('\n\n'.join(review.text for review in reviews))
    await update.message.reply_text(text)
# ----------------------------------------------------------------------------------------------------------------------


def get_review_handlers():
    cancel_handler = get_cancel_handler()

    add_review_handler = ConversationHandler(
        entry_points=[CommandHandler(ADD_REVIEW, add_review, filters=~filters.UpdateType.EDITED_MESSAGE)],
        states={
            ADD_REVIEW_STORY: [CallbackQueryHandler(add_review_story_callback)],
            ADD_REVIEW_RANK: [CallbackQueryHandler(add_review_rank)],
            ADD_REVIEW_CONFIRM: [CallbackQueryHandler(add_review_confirm)],
            ADD_REVIEW_CONFIRM_CALLBACK: [
                CallbackQueryHandler(add_review_confirm_callback, pattern=confirm_pattern(ADD_REVIEW))
            ],
        },
        fallbacks=[cancel_handler],
    )

    list_reviews_handler = CommandHandler(LIST_REVIEWS, list_reviews, filters=~filters.UpdateType.EDITED_MESSAGE)

    return [
        add_review_handler, list_reviews_handler,
    ]
