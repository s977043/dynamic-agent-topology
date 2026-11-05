# 不具合報告: 名前付きの Dict が空のとき as_dict() で {} ではなく [] になる

作業ディレクトリの repository（pyparsing）にある次の不具合を修正してください。

## 症状

`Dict(ZeroOrMore(Group(...)))` に結果名を付けた式で、入力が空（1 組も一致しない）のとき、`as_dict()` の結果の中でその名前の値が `{}` ではなく `[]` になる。1 組以上一致した場合は `{...}` になるため、入力によって値の型が変わる。結果名を付けない場合は空でも `{}` になる。

また、解析結果（`ParseResults`）を `pickle` で保存して読み戻すと、読み戻した結果が元の結果と `==` で等しくならない。読み戻した結果でも、空の名前付き Dict は `as_dict()` で `[]` になる。

## 再現手順

```python
import pickle

import pyparsing as pp

pair = pp.Group(pp.Word(pp.alphas) + pp.Word(pp.nums))
table = pp.Dict(pp.ZeroOrMore(pair))
named = table.copy()("settings")

for text in ["width 10 height 20", ""]:
    print(repr(text), table.parse_string(text).as_dict(), named.parse_string(text).as_dict())

for text in ["width 10", ""]:
    result = named.parse_string(text)
    restored = pickle.loads(pickle.dumps(result))
    print(repr(text), "pickle round trip equal:", restored == result, "| restored as_dict:", restored.as_dict())
```

## 期待結果

- 空の入力でも、名前付きの Dict の値は `as_dict()` で `{}` になる（上の例では `{'settings': {}}`）。1 組以上一致した場合の結果は変わらない
- `pickle` で保存して読み戻した解析結果は、元の結果と `==` で等しく、`as_dict()` の結果も元と同じになる（空の名前付き Dict も `{}`）
- packrat や左再帰の解析を有効にしても同じ結果になる

## 実際の結果

```text
'width 10 height 20' {'width': '10', 'height': '20'} {'settings': {'width': '10', 'height': '20'}}
'' {} {'settings': []}
'width 10' pickle round trip equal: False | restored as_dict: {'settings': {'width': '10'}}
'' pickle round trip equal: False | restored as_dict: {'settings': []}
```

空の名前付き Dict が `[]` になり、pickle で読み戻した結果は元の結果と等しくならない。
