## 症状

`asn1crypto.core` の値を一度 `dump()` したあとに変更し、もう一度 `dump()` しても、値の内部状態 `_mutated` が `True` のまま残ります。入れ子の `Sequence` を含む値では、変更していない子要素も `dump()` のたびにエンコードし直されます。

## 再現手順

```python
from asn1crypto import core

class Ints(core.SequenceOf):
    _child_spec = core.Integer

value = Ints([2, 1])
value.dump()
value.append(3)
print(value.dump(), value._mutated)
```

## 期待結果

- 変更後の `dump()` が変更を反映したエンコードを返し、その後は `_mutated` が `False` になる。`Sequence`・`SequenceOf`・`Set`・`SetOf`、`dump(force=True)`、default 値を持つフィールドの変更でも同じ
- 変更していない子要素は、2 回目以降の `dump()` で再エンコードされず、前回のエンコード結果がそのまま使われる
- 入れ子の子要素を変更した場合は、外側の `dump()` に変更が反映される

## 実際の結果

`dump()` の後も `_mutated` が `True` のまま残ります。
