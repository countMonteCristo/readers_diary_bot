from functools import wraps
import logging

from telegram import CallbackQuery

from config import Config
from entites import User


def reshape(array1d: list, nrows: int, ncols: int) -> list:
    '''
    reshape([1,2,3,4,5,6], 2, 3) -> [[1,2,3], [4,5,6]]
    '''
    # assert len(array1d) >= nrows * ncols
    result = []
    for y in range(nrows):
        row = []
        if y*ncols < len(array1d):
            for x in range(ncols):
                index = y*ncols + x
                if index < len(array1d):
                    row.append(array1d[index])
            result.append(row)
        else:
            break

    return result


def with_db(callable):
    '''Добавляем объекты БД и пользователя к обработчику и при необходимости регистрируем пользователя'''
    db = Config.db()

    @wraps(callable)
    async def f(update, context):
        user = User(update.effective_user)
        db.add_user_if_new(user)
        return await callable(update, context, db, user)

    return f


async def update_confirm_status(query: CallbackQuery, status_msg: str):
    '''Обновляем статус операции в сообщении'''
    if query.message is None:
        logging.error('query.message is None in update_confirm_status')
        return
    await query.edit_message_text(text="{}\n\nСтатус операции: {}".format(query.message.text, status_msg))


if __name__ == '__main__':
    assert reshape([1, 2, 3, 4, 5, 6], 2, 3) == [[1, 2, 3], [4, 5, 6]]
    assert reshape([1, 2, 3, 4, 5, 6], 3, 2) == [[1, 2], [3, 4], [5, 6]]
    assert reshape([1, 2, 3, 4, 5, 6], 2, 2) == [[1, 2], [3, 4]]
    assert reshape([1, 2, 3, 4, 5, 6, 7], 3, 3) == [[1, 2, 3], [4, 5, 6], [7]]
    assert reshape([1, 2, 3, 4, 5, 6, 7], 5, 3) == [[1, 2, 3], [4, 5, 6], [7]]
