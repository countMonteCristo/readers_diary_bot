from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from entities import Story
from utils import reshape

from .kb_utils import callback_args, CancelButton, get_rows_for_cols


def stories_inline_keyboard(stories: List[Story], optional_data=None, add_cancel: bool = True, cols: int = 2):
    story_buttons = [
        InlineKeyboardButton(story.title, callback_data=callback_args(story, optional_data)) for story in stories
    ]
    if add_cancel:
        story_buttons.append(CancelButton)
    rows = get_rows_for_cols(len(story_buttons), cols)
    story_keyboard = reshape(story_buttons, rows, cols)
    story_markup = InlineKeyboardMarkup(story_keyboard)
    return story_markup
