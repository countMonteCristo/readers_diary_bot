from itertools import groupby
from typing import List

from entities import Review


def format_reviews(reviews: List[Review]) -> str:
    author_sep = '-' * 50
    reviews_list = []
    for author_key, author_reviews in groupby(reviews, key=lambda r: r.author_name):
        author_review_list = []
        for story_key, author_story_reviews_group in groupby(author_reviews, key=lambda r: r.story_title):
            rec = '  "{}":\n{}'.format(
                story_key, '\n'.join('    - [{}] {}'.format(r.rank, r.text) for r in author_story_reviews_group)
            )
            author_review_list.append(rec)
        author_rec = '{}:\n{}\n'.format(author_key, ' \n\n'.join(author_review_list))
        reviews_list.append(author_rec)
    reviews_str = f'{author_sep}\n'.join(reviews_list)

    return reviews_str
