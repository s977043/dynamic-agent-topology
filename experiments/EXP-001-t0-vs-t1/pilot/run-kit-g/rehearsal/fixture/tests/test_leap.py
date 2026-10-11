import unittest

from leap import is_leap


class LeapTest(unittest.TestCase):
    def test_divisible_by_four(self):
        self.assertTrue(is_leap(2024))

    def test_century_is_not_leap(self):
        self.assertFalse(is_leap(1900))

    def test_four_hundred_is_leap(self):
        self.assertTrue(is_leap(2000))


if __name__ == "__main__":
    unittest.main()
