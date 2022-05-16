class User:
    def __init__(self, effective_user):
        self.id = effective_user.id
        self.is_bot = effective_user.is_bot
        self.username = effective_user.username
        self.first_name = effective_user.first_name
        self.last_name = effective_user.last_name
        self.lang = effective_user.language_code


class Author:
    def __init__(self, user: User, name: str = '', id_: int = -1):
        self.user_id = user.id
        self.name = name
        self.id = id_


class Story:
    def __init__(self, user: User, title: str = '', id_: int = -1):
        self.user_id = user.id
        self.title = title
        self.author_id = None
        self.author_name = None
        self.id = id_


class Review:
    def __init__(self, user: User):
        self.user_id = user.id
        self.text = None
        self.rank = None
        self.author = None
        self.title = None