## 症状

Trino で秒の小数部が 4 桁以上の `TIMESTAMP` / `TIME` リテラルを変換すると、精度が失われます。

## 再現手順

```python
import sqlglot

print(sqlglot.transpile("SELECT TIMESTAMP '2026-03-01 00:00:00.1234'", read="trino", write="trino")[0])
```

## 期待結果

- `SELECT CAST('2026-03-01 00:00:00.1234' AS TIMESTAMP(4))`
- `TIMESTAMP '2026-03-01 00:00:00.123456789'` は `TIMESTAMP(9)`、`TIMESTAMP '2026-03-01 00:00:00.1234 +02:00'` は `TIMESTAMP(4) WITH TIME ZONE`、`TIME '01:02:03.1234'` は `TIME(4)`

## 実際の結果

`SELECT CAST('2026-03-01 00:00:00.1234' AS TIMESTAMP)`（精度が付かない）
