import sys
import time
from typing import Tuple
import time


class StatusLine(object):
    def __init__(self, width: int):
        self.width = width

        self.outdated: bool = True
        self.string: str = ''

    def update_string(self):
        raise NotImplemented

    def clear(self):
        sys.stdout.write('\r'.ljust(self.width) + '\r')

    def update(self):
        if self.outdated:
            self.update_string()
            self.outdated = False
        sys.stdout.write('\r' + self.string.ljust(self.width))
        sys.stdout.flush()


class StatusBar(object):
    def __init__(self, width: int, surround: Tuple[str, str] = ('[', ']'), with_time: bool = False):
        self.width = width
        self.surround = surround
        self.with_time = with_time
        self.start_time = time.time()
        self.fraction: float = 0.0

    def set(self, value: float) -> 'StatusBar':
        self.fraction = value
        return self

    def __str__(self) -> str:
        if self.with_time:
            time_passed = time.time() - self.start_time
            if self.fraction > 0.0:
                rem = format_seconds((1 - self.fraction)/self.fraction * time_passed)
            else:
                rem = chr(0x221e)
            time_str = f' (t: {format_seconds(time_passed).rjust(7)}, rem.:{rem.rjust(7)})'
        else:
            time_str = ''
        filled = int(self.fraction * self.width)
        extra_eigths = int(8 * (self.fraction * self.width - filled))
        return (self.surround[0] +
                chr(0x2588) * filled +
                (chr(0x2588 + 8 - extra_eigths) if extra_eigths else ' ') +
                ' ' * (self.width - 1 - filled) +
                self.surround[1] +
                time_str)


def format_seconds(seconds: float) -> str:
    if seconds < 2:
        return f'{int(seconds * 1000)} ms'
    elif seconds < 10:
        return f'{seconds:.1f} s'
    elif seconds < 120:
        return f'{int(seconds)} s'
    elif seconds < 60 * 10:
        return f'{seconds / 60:.1f} m'
    elif seconds < 3600 * 2:
        return f'{int(seconds / 60)} m'
    elif seconds < 3600 * 10:
        return f'{seconds / 3600:.1f} h'
    else:
        return f'{int(seconds / 3600)} h'
    
    
def superscript_int(integer: int) -> str:
    return ''.join({'-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
                    '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'}[c] for c in str(integer))
