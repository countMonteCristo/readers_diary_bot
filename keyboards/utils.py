def callback_args(base, optional=None):
    if not optional:
        return (base,)
    else:
        return (base,) + optional
