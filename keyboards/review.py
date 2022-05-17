from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from entities import Review
from utils import reshape

from .kb_utils import callback_args, CancelButton, get_rows_for_cols


def reviews_inline_keyboard(reviews: List[Review], optional_data=None, add_cancel: bool = True, cols: int = 2):
    review_buttons = [
        InlineKeyboardButton(review.text[:15], callback_data=callback_args(review, optional_data)) for review in reviews
    ]
    if add_cancel:
        review_buttons.append(CancelButton)
    rows = get_rows_for_cols(len(review_buttons), cols)
    review_keyboard = reshape(review_buttons, rows, cols)
    review_markup = InlineKeyboardMarkup(review_keyboard)
    return review_markup
