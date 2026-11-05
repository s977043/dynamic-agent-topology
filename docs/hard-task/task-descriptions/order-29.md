# 不具合報告: ParseResults.deepcopy() の結果で、名前付きのグループが元の結果とつながったままになる

作業ディレクトリの repository（pyparsing）にある次の不具合を修正してください。

## 症状

`Group(...)("名前")` のように結果名を付けたグループを含む解析結果を `deepcopy()` で複製すると、複製の中で次のことが起きる。

- 複製の `copy["grp"]`（名前で取り出したもの）と `copy[0]`（位置で取り出したもの）が別のオブジェクトになる
- 名前で取り出したものは複製されておらず、元の結果の `result["grp"]` と同じオブジェクトのままになる
- そのため、複製した後で元の結果のグループを書き換えると、複製を名前でたどった値（`as_dict()` など）も変わってしまう

## 再現手順

```python
import pyparsing as pp

expr = pp.Group(pp.Word(pp.nums)("a") + pp.Word(pp.nums)("b"))("grp") + pp.Word(pp.alphas)("w")
result = expr.parse_string("1 2 xyz")
copy = result.deepcopy()

print("copy['grp'] is copy[0]:", copy["grp"] is copy[0])
print("copy['grp'] is result['grp']:", copy["grp"] is result["grp"])

result["grp"][0] = result["grp"]["a"] = "999"

print("copy.as_list():", copy.as_list())
print("copy.as_dict():", copy.as_dict())
print("copy['grp'].as_dict():", copy["grp"].as_dict())
```

## 期待結果

- 複製の中では、名前で取り出したものと位置で取り出したものが同じオブジェクトになる（`copy['grp'] is copy[0]` が `True`）
- 複製の名前付きの値は元の結果と別のオブジェクトになる（`copy['grp'] is result['grp']` が `False`）
- 元の結果を書き換えても複製は変わらない（`copy.as_list()` は `[['1', '2'], 'xyz']`、`copy.as_dict()` は `{'grp': {'a': '1', 'b': '2'}, 'w': 'xyz'}`、`copy['grp'].as_dict()` は `{'a': '1', 'b': '2'}`）

## 実際の結果

標準出力:

```text
copy['grp'] is copy[0]: False
copy['grp'] is result['grp']: True
copy.as_list(): [['1', '2'], 'xyz']
copy.as_dict(): {'grp': {'a': '999', 'b': '2'}, 'w': 'xyz'}
copy['grp'].as_dict(): {'a': '999', 'b': '2'}
```

位置でたどった値は元のままだが、名前でたどった値には元の結果への書き換え（`'999'`）が現れる。
