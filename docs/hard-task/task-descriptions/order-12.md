# 不具合報告: 値のない変数注釈で宣言した名前を、後から評価される型注釈で使うと警告が誤る

作業ディレクトリの repository（pyflakes）にある次の不具合を修正してください。

## 症状

`T: object` のように値を代入せずに型注釈だけを書いた名前は、実行時には定義されない。この名前を、評価が後回しになる型注釈（引用符で囲んだ注釈、または `from __future__ import annotations` がある場合の注釈）の中で使うと、誤って「undefined name」と報告される。

## 再現手順

```python
import sys
from pyflakes.api import check
from pyflakes.reporter import Reporter

sources = {
    "quoted.py": "T: object\ndef g(t: 'T'): pass\n",
    "future.py": "from __future__ import annotations\nT: object\ndef f(t: T): pass\ndef g(t: 'T'): pass\n",
    "unquoted.py": "T: object\ndef f(t: T): pass\n",
}
for name, src in sources.items():
    n = check(src, name, Reporter(sys.stdout, sys.stdout))
    print(name, "warnings:", n)
```

## 期待結果

- `quoted.py` と `future.py` には警告が出ない（`warnings: 0`）
- すぐに評価される注釈で使う `unquoted.py` では、これまでどおり「undefined name 'T'」が 1 件報告される

## 実際の結果

標準出力:

```text
quoted.py:2:10 undefined name 'T'
quoted.py warnings: 1
future.py:3:10 undefined name 'T'
future.py:4:10 undefined name 'T'
future.py warnings: 2
unquoted.py:2:10 undefined name 'T'
unquoted.py warnings: 1
```

`quoted.py` と `future.py` でも「undefined name 'T'」が報告される。
