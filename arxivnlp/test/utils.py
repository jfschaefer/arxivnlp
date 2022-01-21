import os
import unittest
from typing import Callable


def smart_skip(is_slow: bool = False, requires_data: bool = False) -> Callable[[Callable], Callable]:
    """
        Returns True iff the test should be skipped. This is determined by the system variable ARXIVNLP_TEST
        and the reasons why the test should potentially be skipped (e.g. because it is slow).
    """
    var = 'ARXIVNLP_TEST'
    mode = os.getenv(var)
    if not mode:
        if is_slow:
            return unittest.skip(f'Slow tests are skipped - set {var}=FULL to run all tests.')
        return lambda f: f
    if mode == 'NODATA':
        if requires_data:
            return unittest.skip(f'Tests requiring data are skipped because {var}=NODATA was set.')
        return lambda f: f
    if mode == 'FULL':
        return lambda f: f
    return lambda f: f
