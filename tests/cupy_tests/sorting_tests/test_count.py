import unittest

from cupy import testing


@testing.gpu
class TestCount(unittest.TestCase):

    _multiprocess_can_split_ = True
