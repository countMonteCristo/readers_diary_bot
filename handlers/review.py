from itertools import groupby

from consts import CONFIRM_ANSWERS, CONFIRM_POSITIVE
from db import DB
from entites import Author, Review, Story, User
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
    review_text = ' '.join(context.args)
    if review_text:
        review = Review(user, text=review_text)

        authors = db.list_authors(user)
        author_buttons = [
            InlineKeyboardButton(author.name, callback_data=(author, review)) for author in authors
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

    author: Author
    review: Review
    author, review = query.data

    review.author_name = author.name
    review.author_id = author.id

    stories = db.list_stories(user, author_id=author.id)
    story_buttons = [
        InlineKeyboardButton(story.title, callback_data=(review, story)) for story in stories
    ]
    stories_keyboard = reshape(story_buttons, len(stories) // 2 + len(stories) % 2, 2)
    stories_markup = InlineKeyboardMarkup(stories_keyboard)

    await query.edit_message_text(
        text=f"Выбери произведение автора `{author.name}`",
        reply_markup=stories_markup,
    )
    return ADD_REVIEW_RANK


@with_db
async def add_review_rank(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    await query.answer()

    review: Review
    story: Story
    review, story = query.data

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
    await query.answer()

    review: Review
    rank: int
    review, rank = query.data
    review.rank = rank

    confirm_reply_keyboard = [
        [InlineKeyboardButton(answer, callback_data=(answer, review)) for answer in CONFIRM_ANSWERS]
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

    answer: str
    review: Review
    answer, review = query.data

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
    authors = db.list_authors(user)
    author_buttons = [
        InlineKeyboardButton(author.name, callback_data=author) for author in authors
    ]
    authors_keyboard = reshape(author_buttons, len(authors) // 2 + len(authors) % 2, 2)
    authors_markup = InlineKeyboardMarkup(authors_keyboard)
    await update.message.reply_text('Выбери автора', reply_markup=authors_markup)
    return REMOVE_REVIEW_GET_STORY


@with_db
async def remove_review_get_story(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    await query.answer()

    author: Author = query.data

    stories = db.list_stories(user, author.id)
    stories_buttons = [
        InlineKeyboardButton(story.title, callback_data=(author, story)) for story in stories
    ]
    stories_keyboard = reshape(stories_buttons, len(stories) // 2 + len(stories) % 2, 2)
    stories_markup = InlineKeyboardMarkup(stories_keyboard)

    await query.edit_message_text(
        text=f'Выбери произведение автора {author.name}',
        reply_markup=stories_markup,
    )
    return REMOVE_REVIEW_GET_REVIEW


@with_db
async def remove_review_get_review(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    await query.answer()

    author: Author
    story: Story
    author, story = query.data

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
    await query.answer()

    author: Author
    story: Story
    review: Review
    author, story, review = query.data

    confirm_reply_keyboard = [
        [InlineKeyboardButton(answer, callback_data=(answer, review)) for answer in CONFIRM_ANSWERS]
    ]
    confirm_markup = InlineKeyboardMarkup(confirm_reply_keyboard)

    await query.edit_message_text(
        text=f"Удалить отзыв на произведение `{story.title}` автора `{author.name}`?",
        reply_markup=confirm_markup,
    )
    return REMOVE_REVIEW_CONFIRM_CALLBACK


@with_db
async def remove_review_confirm_callback(update: Update, context: CallbackContext.DEFAULT_TYPE, db: DB, user: User):
    query = update.callback_query
    await query.answer()

    answer: str
    review: Review
    answer, review = query.data
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
