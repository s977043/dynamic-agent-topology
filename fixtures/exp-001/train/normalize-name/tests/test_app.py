import unittest
from app import normalize_name

class NormalizeNameTest(unittest.TestCase):
    def test_trims_and_lowercases(self):
        self.assertEqual(normalize_name("  Alice  "), "alice")

    def test_preserves_empty_string(self):
        self.assertEqual(normalize_name("   "), "")

if __name__ == "__main__":
    unittest.main()
