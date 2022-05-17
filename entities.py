INVALID_ID = -1


class User:
    def __init__(self, effective_user):
        self.id = effective_user.id
        self.is_bot = effective_user.is_bot
        self.username = effective_user.username
        self.first_name = effective_user.first_name
        self.last_name = effective_user.last_name
        self.lang = effective_user.language_code


class Author:
    def __init__(self, user: User, name: str = '', id_: int = INVALID_ID):
        self.user_id = user.id
        self.name = name
        self.id = id_


class Story:
    def __init__(self, user: User, title: str = '', id_: int = INVALID_ID, author_name: str = ''):
        self.user_id = user.id
        self.title = title
        self.author_id = INVALID_ID
        self.author_name = author_name
        self.id = id_


class Review:
    def __init__(
        self, user: User, text: str, id_: int = INVALID_ID, author_name: str = '',
        story_title: str = '', rank: int = INVALID_ID,
    ):
        self.user_id = user.id
        self.text = text
        self.rank = rank
        self.author_name = author_name
        self.author_id = INVALID_ID
        self.story_id = INVALID_ID
        self.story_title = story_title
        self.id = id_

    def __str__(self):
        return f'Review(title="{self.story_title}",text="{self.text}",author="{self.author_name}",rank={self.rank})'

    def __repr__(self):
        return str(self)
