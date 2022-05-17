from entites import User
from config import Config
from consts import CONFIRM_ANSWERS

from functools import wraps
from collections.abc import Iterable

from telegram import CallbackQuery


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
    await query.edit_message_text(text="{}\n\nСтатус операции: {}".format(query.message.text, status_msg))


def confirm_pattern(label: str):
    def callable_pattern(data: CallbackQuery.data):
        if isinstance(data, Iterable):
            # if callback data is iterable, it should be in form of
            # answer, {useful_data...}, label
            return data[0] in CONFIRM_ANSWERS and data[-1] == label
        else:
            return data in CONFIRM_ANSWERS
    return callable_pattern


if __name__ == '__main__':
    assert reshape([1, 2, 3, 4, 5, 6], 2, 3) == [[1, 2, 3], [4, 5, 6]]
    assert reshape([1, 2, 3, 4, 5, 6], 3, 2) == [[1, 2], [3, 4], [5, 6]]
    assert reshape([1, 2, 3, 4, 5, 6], 2, 2) == [[1, 2], [3, 4]]
    assert reshape([1, 2, 3, 4, 5, 6, 7], 3, 3) == [[1, 2, 3], [4, 5, 6], [7]]
    assert reshape([1, 2, 3, 4, 5, 6, 7], 5, 3) == [[1, 2, 3], [4, 5, 6], [7]]
