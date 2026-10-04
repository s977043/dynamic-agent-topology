import unittest
from app import safe_divide

class SafeDivideTest(unittest.TestCase):
    def test_zero_division_contract(self):
        self.assertEqual(safe_divide(3, 0), 0.0)

    def test_regular_division(self):
        self.assertEqual(safe_divide(6, 2), 3.0)

if __name__ == "__main__":
    unittest.main()
