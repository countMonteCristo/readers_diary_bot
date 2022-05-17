from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from utils import reshape

from .kb_utils import callback_args, get_rows_for_cols, CancelButton


def rank_inline_keyboard(optional_data=None, add_cancel: bool = True, cols: int = 3):
    rank_buttons = [
        InlineKeyboardButton(str(rank), callback_data=callback_args(rank, optional_data)) for rank in range(1, 6)
    ]
    if add_cancel:
        rank_buttons.append(CancelButton)
    rows = get_rows_for_cols(len(rank_buttons), cols)
    rank_keyborad = reshape(rank_buttons, rows, cols)
    rank_markup = InlineKeyboardMarkup(rank_keyborad)

    return rank_markup
