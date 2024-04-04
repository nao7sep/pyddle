# Created: 2024-04-04
# Just a bunch of utility functions.

def get_not_none(*args):
    for arg in args:
        if arg is not None:
            return arg

    return None

def get_not_none_or_call_func(func, *args):
    for arg in args:
        if arg is not None:
            return arg

    return func()
