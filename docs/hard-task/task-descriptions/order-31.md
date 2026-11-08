# 不具合報告: typing.cast と TypeVar の呼び出しで、未定義名と未使用 import の報告が誤る

作業ディレクトリの repository（pyflakes）にある次の不具合を修正してください。

## 症状

`typing.cast(...)` と `typing.TypeVar(...)` の呼び出しを含むコードを pyflakes で検査すると、次の誤りが起きる。

- `cast` の型をキーワード引数（`typ='Optional[int]'`）の文字列で渡すと、その文字列の中で使っている名前が使われたものとして扱われず、「imported but unused」が報告される
- `cast` の第 1 引数に未定義の名前を書くと、同じ未定義名の報告が 1 回ではなく 2 回出る
- `TypeVar` の `default=` に文字列で型を渡すと、その文字列の中で使っている名前が使われたものとして扱われず、「imported but unused」が報告される
- `TypeVar` の第 1 引数に未定義の名前を書いても、未定義名が報告されない

## 再現手順

```python
import io
from pyflakes.api import check
from pyflakes.reporter import Reporter

cases = {
    "A": "from typing import cast, Optional\ncast(typ='Optional[int]', val=42)\n",
    "B": "from typing import cast\ncast(undefined, 0)\n",
    "C": "from typing import TypeVar, Optional\nT = TypeVar('T', default='Optional[int]')\n",
    "D": "from typing import TypeVar\n\nT = TypeVar(T, int)\n",
}
for name, src in cases.items():
    out, err = io.StringIO(), io.StringIO()
    check(src, f"{name}.py", Reporter(out, err))
    print(f"--- {name}")
    print(out.getvalue() + err.getvalue(), end="")
```

## 期待結果

- A: 何も報告されない（`Optional` は型の文字列の中で使われている）
- B: `undefined name 'undefined'` が 1 回だけ報告される
- C: 何も報告されない（`Optional` は `default=` の型の文字列の中で使われている）
- D: 第 1 引数の未定義の名前 `T` について `undefined name 'T'` が報告される

## 実際の結果

標準出力:

```text
--- A
A.py:1:1: 'typing.Optional' imported but unused
--- B
B.py:2:6: undefined name 'undefined'
B.py:2:6: undefined name 'undefined'
--- C
C.py:1:1: 'typing.Optional' imported but unused
--- D
```

A と C では未使用 import が誤って報告され、B では同じ未定義名が 2 回報告され、D では何も報告されない。
