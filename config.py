import os


class Config:
    @staticmethod
    def token():
        return os.environ['BOT_TOKEN']

    @staticmethod
    def db():
        return os.environ['BOT_DB']
