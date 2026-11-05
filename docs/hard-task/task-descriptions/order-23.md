# 不具合報告: Transformer の派生クラスの一部で、トークン用のコールバックを定義すると変換が失敗する

作業ディレクトリの repository（lark）にある次の不具合を修正してください。

## 症状

`Tree` を変換するクラスを lark の Transformer 系の基底クラスから派生させ、規則名のメソッド（例: `add`）とトークン型名のメソッド（例: `N`）を定義する。`Transformer`・`Transformer_InPlace`・`Transformer_InPlaceRecursive` から派生させた場合は期待どおりに変換されるが、`Transformer_NonRecursive` から派生させた場合だけ、同じ木の変換が例外で失敗する。

## 再現手順

```python
from lark import Tree, Token
from lark.visitors import (Transformer, Transformer_InPlace,
                           Transformer_NonRecursive, Transformer_InPlaceRecursive)

for base in (Transformer, Transformer_InPlace,
             Transformer_NonRecursive, Transformer_InPlaceRecursive):
    class Calc(base):
        def add(self, children):
            return sum(children)

        def N(self, token):
            return int(token)

    tree = Tree("start", [Tree("add", [Token("N", "1"), Token("N", "2")]),
                          Tree("add", [Token("N", "3"), Token("N", "4")])])
    try:
        print(base.__name__, Calc().transform(tree))
    except Exception as e:
        print(base.__name__, "raised", type(e).__name__)
```

## 期待結果

- 4 つの基底クラスのどれから派生させても変換に成功し、同じ解析結果を返す

## 実際の結果

標準出力:

```text
Transformer Tree('start', [3, 7])
Transformer_InPlace Tree('start', [3, 7])
Transformer_NonRecursive raised VisitError
Transformer_InPlaceRecursive Tree('start', [3, 7])
```

`Transformer_NonRecursive` から派生させた場合だけ、変換が `VisitError` で失敗する。
