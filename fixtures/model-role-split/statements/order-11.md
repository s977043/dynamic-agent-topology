## 症状

PostgreSQL の前方一致の演算子 `^@` が、べき乗とパラメータとして解釈されます。

## 再現手順

```python
import sqlglot

print(sqlglot.transpile("a ^@ b", read="postgres", write="postgres")[0])
```

## 期待結果

`STARTS_WITH(a, b)`

## 実際の結果

`POWER(a, $b)`
