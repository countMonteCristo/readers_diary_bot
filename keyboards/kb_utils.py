from telegram import InlineKeyboardButton


def callback_args(base, optional=None):
    if not optional:
        return (base,)
    else:
        return (base,) + optional


def get_rows_for_cols(length: int, cols: int) -> int:
    '''Calculate minimal `rows` such that rows*cols >= length'''
    rows = length // cols + int(length % cols > 0)
    return rows


CANCEL_VALUE = object()


CancelButton = InlineKeyboardButton('Отмена', callback_data=CANCEL_VALUE)
