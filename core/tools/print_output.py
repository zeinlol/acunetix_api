from datetime import datetime
from typing import NoReturn


def timed_print(string: str) -> NoReturn:
    print(f'{datetime.now()}: {string}')
