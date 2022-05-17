from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from consts import CONFIRM_ANSWERS

from .utils import callback_args


def confirm_inline_keyboard(optional_data=None):
    confirm_reply_keyboard = [
        [InlineKeyboardButton(text, callback_data=callback_args(text, optional_data)) for text in CONFIRM_ANSWERS]
    ]
    confirm_markup = InlineKeyboardMarkup(confirm_reply_keyboard)
    return confirm_markup
