import logging
import sqlite3

from entities import INVALID_ID, Author, Review, Story, User


class DB:
    def __init__(self, sqlite_fn, debug=False):
        self.conn = sqlite3.connect(sqlite_fn)
        if debug:
            self.conn.set_trace_callback(logging.info)

    def __del__(self):
        self.conn.close()

    def prepare(self):
        cursor = self.conn.cursor()
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS user
            (
                id INTEGER PRIMARY KEY
            )
            '''
        )

        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS author
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                FOREIGN KEY(user_id) REFERENCES user(id)
            )
            '''
        )

        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS story
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                author_id INTEGER,
                FOREIGN KEY(author_id) REFERENCES author(id),
                FOREIGN KEY(user_id) REFERENCES user(id)
            )
            '''
        )

        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS review
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                story_id INTEGER,
                text TEXT NOT NULL,
                rank INTEGER NOT NULL CHECK(rank >= 0 AND rank <= 5),
                FOREIGN KEY(user_id) REFERENCES user(id),
                FOREIGN KEY(story_id) REFERENCES story(id)
            )
            '''
        )

        # Create triggers
        cursor.execute(
            '''
            CREATE TRIGGER IF NOT EXISTS on_author_delete
            AFTER DELETE ON author
            FOR EACH ROW
            BEGIN
                DELETE FROM story WHERE story.user_id == OLD.user_id AND story.author_id == OLD.id;
            END
            '''
        )
        cursor.execute(
            '''
            CREATE TRIGGER IF NOT EXISTS on_story_delete
            AFTER DELETE ON story
            FOR EACH ROW
            BEGIN
                DELETE FROM review WHERE review.user_id == OLD.user_id AND review.story_id == OLD.id;
            END
            '''
        )

        self.conn.commit()

    def add_user_if_new(self, user: User):
        cursor = self.conn.cursor()
        users = cursor.execute(
            '''SELECT * FROM user WHERE user.id == ?''', (user.id,)
        ).fetchall()
        if len(users) == 0:
            cursor.execute(
                '''INSERT INTO user VALUES (?)''', (user.id,)
            )
            self.conn.commit()
            logging.debug(f'Add new user: {user.username}')
        else:
            logging.debug(f'User with {user.id=} already in db')

    def add_author(self, author: Author):
        cursor = self.conn.cursor()
        cursor.execute(
            '''INSERT INTO author (user_id, name) VALUES (?, ?)''',
            (author.user_id, author.name)
        )
        self.conn.commit()

    def author_id(self, user: User, author_name: str):
        cursor = self.conn.cursor()
        authors = cursor.execute(
            '''SELECT id FROM author WHERE user_id == ? AND name == ?''',
            (user.id, author_name)
        ).fetchall()
        if len(authors) > 1:
            # TODO: emit some signal if that happens
            logging.critical(f'[{user.id=}] More than one unique author: `{author_name}`')
            return authors[0]
        return INVALID_ID if not authors else authors[0]

    def list_authors(self, user: User):
        cursor = self.conn.cursor()
        authors = cursor.execute(
            '''SELECT id, name FROM author WHERE user_id == ?''',
            (user.id,)
        ).fetchall()
        return [Author(user, name=row[1], id_=row[0]) for row in authors]

    def remove_author(self, user: User, author_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            '''DELETE FROM author WHERE user_id == ? AND id == ?''',
            (user.id, author_id)
        )
        self.conn.commit()

    def add_story(self, story: Story):
        cursor = self.conn.cursor()
        cursor.execute(
            '''INSERT INTO story (user_id, title, author_id) VALUES (?, ?, ?)''',
            (story.user_id, story.title, story.author_id)
        )
        self.conn.commit()

    def story_id(self, user: User, story: Story, author: Author):
        cursor = self.conn.cursor()
        stories = cursor.execute(
            '''SELECT id FROM story WHERE user_id == ? AND author_id == ? AND title == ?''',
            (user.id, author.id, story.title)
        ).fetchall()
        if len(stories) > 1:
            # TODO: emit some signal if that happens
            logging.critical(f'[{user.id=}] More than one unique story `{story.title}` for author `{author.name}`')
            return stories[0]
        return INVALID_ID if not stories else stories[0]

    def list_stories(self, user: User, author_id: int = INVALID_ID):
        cursor = self.conn.cursor()
        if author_id == INVALID_ID:
            stories = cursor.execute(
                '''
                    SELECT story.title, story.id, author.name
                    FROM story
                    JOIN author ON (story.user_id == author.user_id) AND (story.author_id == author.id)
                    WHERE story.user_id == ?
                    ORDER BY author.name, story.title
                ''',
                (user.id,)
            ).fetchall()
        else:
            stories = cursor.execute(
                '''
                    SELECT story.title, story.id, author.name
                    FROM story
                    JOIN author ON (story.user_id == author.user_id) AND (story.author_id == author.id)
                    WHERE story.user_id == ? AND story.author_id == ?
                    ORDER BY story.title
                ''',
                (user.id, author_id)
            ).fetchall()
        return [Story(user, title=row[0], id_=row[1], author_name=row[2]) for row in stories]

    def remove_story(self, user: User, story_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            '''DELETE FROM story WHERE user_id == ? AND id == ?''',
            (user.id, story_id)
        )
        self.conn.commit()

    def add_review(self, review: Review):
        cursor = self.conn.cursor()
        cursor.execute(
            '''INSERT INTO review (user_id, story_id, text, rank) VALUES (?, ?, ?, ?)''',
            (review.user_id, review.story_id, review.text, review.rank)
        )
        self.conn.commit()

    def list_reviews(self, user: User, author_id: int = INVALID_ID):
        cursor = self.conn.cursor()
        if author_id == INVALID_ID:
            reviews = cursor.execute(
                '''
                    SELECT review.text, review.id, story.title, author.name, review.rank
                    FROM review
                    JOIN story ON (review.user_id == story.user_id) AND (review.story_id == story.id)
                    JOIN author ON (review.user_id == author.user_id) AND (story.author_id == author.id)
                    WHERE review.user_id == ?
                    ORDER BY author.name, story.title, review.text
                ''',
                (user.id,)
            ).fetchall()
        else:
            reviews = cursor.execute(
                '''
                    SELECT review.text, review.id, story.title, author.name, review.rank
                    FROM review
                    JOIN story ON (review.user_id == story.user_id) AND (review.story_id == story.id)
                    JOIN author ON (review.user_id == author.user_id) AND (story.author_id == author.id)
                    WHERE review.user_id == ? AND story.author_id == ?
                    ORDER BY author.name, story.title, review.text
                ''',
                (user.id, author_id)
            ).fetchall()
        return [
            Review(user, text=row[0], id_=row[1], story_title=row[2], author_name=row[3], rank=row[4])
            for row in reviews
        ]

    def list_story_reviews(self, user: User, story_id: int):
        cursor = self.conn.cursor()
        reviews = cursor.execute(
            '''
                SELECT review.text, review.id, story.title, author.name, review.rank
                FROM review
                JOIN story ON (review.user_id == story.user_id) AND (review.story_id == story.id)
                JOIN author ON (review.user_id == author.user_id) AND (story.author_id == author.id)
                WHERE review.user_id == ? AND story.id == ?
                ORDER BY author.name, story.title, review.text
            ''',
            (user.id, story_id)
        ).fetchall()
        return [
            Review(user, text=row[0], id_=row[1], story_title=row[2], author_name=row[3], rank=row[4])
            for row in reviews
        ]

    def remove_review(self, user: User, review_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            '''DELETE FROM review WHERE user_id == ? AND id == ?''',
            (user.id, review_id)
        )
        self.conn.commit()


if __name__ == '__main__':
    db = DB(':memory:')
    db.prepare()

    cursor = db.conn.cursor()
    cursor.execute(
        '''
        INSERT INTO user VALUES (7155816)
        '''
    )

    for row in cursor.execute('SELECT * from user'):
        print(row)
