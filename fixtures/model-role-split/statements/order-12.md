## 症状

`more_itertools.bucket` に、偽と評価される（falsey な）callable を validator として渡すと、validator が無視されて既定の動作になります。

## 再現手順

```python
import more_itertools as mi

class AllowedKeys(set):
    def __call__(self, key):
        return key in self

D = mi.bucket(iter([10, 20, 11, 21]), key=lambda x: x, validator=AllowedKeys())
print(list(D[10]), 10 in D, set(D))
```

## 期待結果

`[] False set()`（空の validator はどの key も許さない）

## 実際の結果

`list(D[10])` が `[10]` になります。
