from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from entites import Story
from utils import reshape

from .kb_utils import callback_args


def stories_inline_keyboard(stories: List[Story], optional_data=None):
    story_buttons = [
        InlineKeyboardButton(story.title, callback_data=callback_args(story, optional_data)) for story in stories
    ]
    story_keyboard = reshape(story_buttons, len(stories) // 2 + len(stories) % 2, 2)
    story_markup = InlineKeyboardMarkup(story_keyboard)
    return story_markup
