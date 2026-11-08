# 不具合報告: 文字列で書いた型注釈の中でだけ使っている import が「未使用」と報告される

作業ディレクトリの repository（pyflakes）にある次の不具合を修正してください。

## 症状

`typing` の型（`Optional[...]`、`Callable[...]` など）の添字の中や、`typing.cast()` の第 1 引数に、型を文字列（引用符付き）で書くと、その文字列の中で使っている名前が型注釈として扱われない。その結果、その名前を文字列の中でだけ使っている import が「imported but unused」と報告される。

## 再現手順

```python
import sys
from pyflakes.api import check
from pyflakes.reporter import Reporter

sources = {
    "optional.py": "from queue import Queue\nfrom typing import Optional\n\nMaybeQueue = Optional['Queue[str]']\n",
    "callable.py": "from queue import Queue\nfrom typing import Callable\n\nFunc = Callable[['Queue[str]'], None]\n",
    "cast.py": "from typing import cast, Optional\n\nmaybe_int = cast('Optional[int]', 42)\n",
    "cast_renamed.py": "from typing import cast as tcast, Optional\n\nmaybe_int = tcast('Optional[int]', 42)\n",
}
for name, src in sources.items():
    n = check(src, name, Reporter(sys.stdout, sys.stdout))
    print(name, "warnings:", n)
```

## 期待結果

- 4 つのソースのどれにも警告が出ない（`warnings: 0`）
- 文字列の中の名前は、型注釈の中に直接書いた場合と同じように「使われている」と判定される

## 実際の結果

標準出力:

```text
optional.py:1:1 'queue.Queue' imported but unused
optional.py warnings: 1
callable.py:1:1 'queue.Queue' imported but unused
callable.py warnings: 1
cast.py:1:1 'typing.Optional' imported but unused
cast.py warnings: 1
cast_renamed.py:1:1 'typing.Optional' imported but unused
cast_renamed.py warnings: 1
```
