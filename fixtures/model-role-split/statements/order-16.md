## 症状

ClickHouse の bit 演算の集約関数 `groupBitAnd` / `groupBitOr` / `groupBitXor` が、他の dialect の bit 演算の集約と対応付けられていません。

## 再現手順

```python
import sqlglot

print(sqlglot.transpile("BITWISE_AND_AGG(x)", write="clickhouse")[0])
print(sqlglot.transpile("groupBitAnd(x)", read="clickhouse", write="duckdb")[0])
```

## 期待結果

- 既定の dialect の `BITWISE_AND_AGG(x)`、DuckDB / PostgreSQL の `BIT_AND(x)` は、ClickHouse で `groupBitAnd(x)`。OR・XOR も同じ（`groupBitOr`・`groupBitXor`）
- ClickHouse の `groupBitAnd(x)` は、DuckDB / PostgreSQL で `BIT_AND(x)`
- `groupBitAndIf(x, y)` は従来どおり combinator 付きの集約（`exp.CombinedAggFunc`）として扱う
- `groupBitAnd(x) OVER (PARTITION BY y)` は、window の中身を `exp.BitwiseAndAgg` として parse する

## 実際の結果

ClickHouse への出力が `BITWISE_AND_AGG(x)` のままです。
