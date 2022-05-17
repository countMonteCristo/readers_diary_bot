from typing import List

from entities import Author


def format_authors(authors: List[Author]) -> str:
    return '\n'.join(author.name for author in authors)
