"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

import time


def wait_for(proc, timeout=3600):
    """Wait for a true condition supplied via function or closure"""
    for delta in range(0, timeout):
        if proc():
            return delta
        else:
            time.sleep(1)
    raise RuntimeError


# vi: ts=4 et:
