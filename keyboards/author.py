from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from entities import Author
from utils import reshape

from .kb_utils import callback_args, get_rows_for_cols, CancelButton


def authors_inline_keyboard(authors: List[Author], optional_data=None, add_cancel: bool = True, cols: int = 2):
    author_buttons = [
        InlineKeyboardButton(author.name, callback_data=callback_args(author, optional_data)) for author in authors
    ]
    if add_cancel:
        author_buttons.append(CancelButton)
    rows = get_rows_for_cols(len(author_buttons), cols)
    author_keyboard = reshape(author_buttons, rows, cols)
    author_markup = InlineKeyboardMarkup(author_keyboard)
    return author_markup
