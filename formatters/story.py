from itertools import groupby
from typing import List

from entities import Story


def format_stories(stories: List[Story]) -> str:
    stories_list = []
    for key, author_stories in groupby(stories, key=lambda story: story.author_name):
        author_story_lits = '{}:\n{}'.format(key, '\n'.join('    {}'.format(story.title) for story in author_stories))
        stories_list.append(author_story_lits)
    stories_str = '\n\n'.join(stories_list)
    return stories_str
