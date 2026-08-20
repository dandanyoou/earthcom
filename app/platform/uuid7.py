import secrets
import threading
import time
from uuid import UUID

_RANDOM_BITS = 74
_RANDOM_MASK = (1 << _RANDOM_BITS) - 1
_TIMESTAMP_MASK = (1 << 48) - 1
_lock = threading.Lock()
_last_milliseconds = -1
_last_random = -1


def new_uuid7() -> UUID:
    global _last_milliseconds, _last_random

    with _lock:
        milliseconds = time.time_ns() // 1_000_000
        if milliseconds > _last_milliseconds:
            random_bits = secrets.randbits(_RANDOM_BITS)
        else:
            milliseconds = _last_milliseconds
            random_bits = (_last_random + 1) & _RANDOM_MASK
            if random_bits == 0:
                milliseconds += 1

        _last_milliseconds = milliseconds
        _last_random = random_bits

    random_a = random_bits >> 62
    random_b = random_bits & ((1 << 62) - 1)
    value = (
        ((milliseconds & _TIMESTAMP_MASK) << 80)
        | (0x7 << 76)
        | (random_a << 64)
        | (0b10 << 62)
        | random_b
    )
    return UUID(int=value)
