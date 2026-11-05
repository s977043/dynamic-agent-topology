# 不具合報告: 注釈の中の TypedDict / NamedTuple の名前が未定義名として報告される

作業ディレクトリの repository（pyflakes）にある次の不具合を修正してください。

## 症状

型注釈の中（`List[...]` などの添字の中や、クラス本体の変数注釈）で `TypedDict(...)` や `NamedTuple(...)` を関数形式で書くと、型の名前として渡した文字列（例: `'Inner'`、`'Row'`）や、TypedDict の辞書のキー（例: `'v'`）が前方参照として解釈され、`undefined name` が報告される。これらは型の名前やフィールド名であって、型の参照ではない。

## 再現手順

```python
import sys
from pyflakes.api import check
from pyflakes.reporter import Reporter

sources = {
    "ok.py": (
        "from typing import List, NamedTuple, TypedDict\n"
        "\n"
        "class Point(TypedDict):\n"
        "    inner: TypedDict('Inner', {'v': int})\n"
        "\n"
        "rows: List[NamedTuple('Row', [('id', int)])]\n"
        "cols: List[TypedDict('Col', name=str)]\n"
    ),
    "undefined.py": (
        "from typing import List, NamedTuple\n"
        "\n"
        "rows: List[NamedTuple('Row', [('id', 'Missing')])]\n"
    ),
}
reporter = Reporter(sys.stdout, sys.stdout)
for filename, src in sources.items():
    print("#", filename, "warnings:", check(src, filename, reporter))
```

## 期待結果

- `ok.py` では警告が 0 件になる
- `undefined.py` では、フィールドの型として文字列で書いた `'Missing'` だけが `undefined name 'Missing'` として報告される（型の名前 `'Row'` は報告されない）
- 型として書かれた部分（TypedDict の値、NamedTuple のフィールドの型、TypeVar の bound や制約、`cast` の型の引数）は、注釈の中でも外でも型注釈として検査され、その中の文字列は前方参照として扱われる

## 実際の結果

```text
ok.py:4:22 undefined name 'Inner'
ok.py:4:32 undefined name 'v'
ok.py:6:23 undefined name 'Row'
ok.py:7:22 undefined name 'Col'
# ok.py warnings: 4
undefined.py:3:23 undefined name 'Row'
undefined.py:3:38 undefined name 'Missing'
# undefined.py warnings: 2
```

型の名前と TypedDict のキーが未定義名として報告される。
