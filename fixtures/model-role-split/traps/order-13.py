

class TestQuotedTypeVarArguments(TestCase):

    def test_quoted_typevar_bound_import(self):
        self.flakes("""
        from typing import TypeVar, Optional

        T = TypeVar('T', bound='Optional[int]')
        """, m.UnusedImport)
