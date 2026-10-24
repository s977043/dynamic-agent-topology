

class DumpStateTests(unittest.TestCase):

    def test_mutated_flag_after_dump(self):
        value = SequenceOfInts([2, 1])
        value.dump()
        value.append(3)
        value.dump()
        self.assertTrue(value._mutated)
