from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from entites import Author
from utils import reshape

from .kb_utils import callback_args


def authors_inline_keyboard(authors: List[Author], optional_data=None):
    author_buttons = [
        InlineKeyboardButton(author.name, callback_data=callback_args(author, optional_data)) for author in authors
    ]
    author_keyboard = reshape(author_buttons, len(authors) // 2 + len(authors) % 2, 2)
    author_markup = InlineKeyboardMarkup(author_keyboard)
    return author_markup
