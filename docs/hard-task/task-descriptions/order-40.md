# 不具合報告: running_min / running_max が等しい値のとき組み込みの min / max と違う要素を返す

作業ディレクトリの repository（more-itertools）にある次の不具合を修正してください。

## 症状

`running_min` と `running_max` に `maxlen` を指定すると、ウィンドウ内に等しい値が複数あるとき、組み込みの `min` / `max` とは違う要素を返す。組み込みの `min(x, y)` / `max(x, y)` は、`x == y` のとき先に現れた `x` を返すが、`running_min` / `running_max` は後から来た要素を返す。`5`、`5.0`、`Decimal(5)` のように、等しいが型の違う値を流すと違いが見える。

## 再現手順

```python
from decimal import Decimal

import more_itertools as mi

data = [5, 5.0, Decimal(5), 5]
k = 3
windows = [data[max(0, i - k + 1):i + 1] for i in range(len(data))]
for name, func, builtin in [("running_min", mi.running_min, min),
                            ("running_max", mi.running_max, max)]:
    print(name, [repr(v) for v in func(data, maxlen=k)])
    print("builtin", [repr(builtin(w)) for w in windows])
```

## 期待結果

- `maxlen` を指定した `running_min(data, maxlen=k)` / `running_max(data, maxlen=k)` の各値は、それぞれのウィンドウに対する組み込みの `min` / `max` の結果と同じ要素になる（等しい値が複数あるときは、ウィンドウ内で先に現れた要素）
- 上の再現コードでは、`running_min` と `running_max` の行が、どちらも直後の `builtin` の行と一致する

## 実際の結果

```text
running_min ['5', '5.0', "Decimal('5')", '5']
builtin ['5', '5', '5', '5.0']
running_max ['5', '5.0', "Decimal('5')", '5']
builtin ['5', '5', '5', '5.0']
```

等しい値のとき、`running_min` / `running_max` は最後に来た要素を返し、組み込みの `min` / `max` と一致しない。
