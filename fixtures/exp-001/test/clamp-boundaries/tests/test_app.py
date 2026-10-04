import unittest
from app import clamp

class ClampTest(unittest.TestCase):
    def test_low_boundary(self):
        self.assertEqual(clamp(-2, 0, 10), 0)

    def test_high_boundary(self):
        self.assertEqual(clamp(12, 0, 10), 10)

    def test_in_range(self):
        self.assertEqual(clamp(5, 0, 10), 5)

if __name__ == "__main__":
    unittest.main()
