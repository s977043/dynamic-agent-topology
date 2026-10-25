## 症状

`typing.TypeVar` の制約や `bound` に文字列で書いた型注釈の中の名前が、使用として数えられません。そのため、その名前の import が未使用と報告されます。

## 再現手順

```python
from pyflakes.api import check
from pyflakes.reporter import _makeDefaultReporter

check("""
from typing import TypeVar, Optional, List

T = TypeVar('T', bound='Optional[int]')
S = TypeVar('S', int, bound='List[int]')
U = TypeVar('U', 'str', 'Optional[int]', bytes)
""", "example.py", _makeDefaultReporter())
```

## 期待結果

警告なし

## 実際の結果

`'typing.Optional' imported but unused` などの未使用 import の警告が出ます。
