import os

from db import DB


class Config:
    _db = DB(os.environ['BOT_DB'], debug=os.environ.get('BOT_DEBUG_SQL'))

    @staticmethod
    def token():
        return os.environ['BOT_TOKEN']

    @classmethod
    def db(cls):
        return cls._db
