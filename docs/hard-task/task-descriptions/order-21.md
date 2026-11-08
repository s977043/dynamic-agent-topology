# 不具合報告: 既定値付きの TypeVar を使った Generic の添字指定が PEP 696 どおりに動かない

作業ディレクトリの repository（typing_extensions）にある次の不具合を修正してください。

## 症状

Python 3.12 で、`typing_extensions.TypeVar` に `default=` を付けた型変数（PEP 696）を `typing.Generic` と組み合わせると、次の 2 つが PEP 696 の規定と合わない。

- 既定値のある型変数の後に既定値のない型変数を並べた `Generic[...]` が、エラーにならずに作れてしまう
- 既定値のある型変数を最後に持つジェネリッククラスで、既定値のある引数を省略して添字を付けると `TypeError` になる

## 再現手順

```python
from typing import Generic
from typing_extensions import TypeVar

T = TypeVar("T")
U = TypeVar("U")
DefaultStrT = TypeVar("DefaultStrT", default=str)

try:
    print("Generic[DefaultStrT, T] ->", Generic[DefaultStrT, T])
except TypeError:
    print("Generic[DefaultStrT, T] -> TypeError")

class A(Generic[T, U, DefaultStrT]): ...

for label, build in [
    ("A[int, bool]", lambda: A[int, bool]),
    ("A[int, bool, str]", lambda: A[int, bool, str]),
    ("A[int]", lambda: A[int]),
]:
    try:
        print(label, "->", build())
    except TypeError:
        print(label, "-> TypeError")
```

## 期待結果

- `Generic[DefaultStrT, T]`（既定値のある型変数の後に既定値のない型変数）は `TypeError` になる
- `A[int, bool]` は、省略した最後の引数に既定値を使うものとして受理される
- `A[int, bool, str]` は今と同じく受理される
- `A[int]` は、引数が足りないため今と同じく `TypeError` になる

## 実際の結果

標準出力:

```text
Generic[DefaultStrT, T] -> typing.Generic[~DefaultStrT, ~T]
A[int, bool] -> TypeError
A[int, bool, str] -> __main__.A[int, bool, str]
A[int] -> TypeError
```

`Generic[DefaultStrT, T]` はエラーにならず、`A[int, bool]` は `TypeError` になる。
