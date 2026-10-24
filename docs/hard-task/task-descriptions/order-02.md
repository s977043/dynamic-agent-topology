# 不具合報告: 比較演算子と IS 述語が並ぶ式の結合順序が方言の仕様と合わない

作業ディレクトリの repository（sqlglot）にある次の不具合を修正してください。

## 症状

`a = b IS NULL` のように比較演算子の後に IS 述語（`IS NULL`、`IS NOT NULL`、`IS TRUE` など）が続く式を解析すると、方言によらず `a = (b IS NULL)` として解析される。PostgreSQL・DuckDB・MySQL などでは、この式は `(a = b) IS NULL` と評価されるため、解析結果の木が実際の意味と異なる。

## 再現手順

```python
from sqlglot import parse_one

for d in ["postgres", "duckdb", "mysql", "snowflake"]:
    e = parse_one("a = b IS NULL", read=d)
    print(d, type(e).__name__, type(e.expression).__name__)
```

## 期待結果

- 解析結果が、それぞれの方言でその式が実際に評価される意味と一致する
- 解析した式を SQL に戻したとき、元の意味が保たれる

## 実際の結果

```text
postgres EQ Is
duckdb EQ Is
mysql EQ Is
snowflake EQ Is
```

すべての方言で、最上位が `EQ`、その右側が `Is`（`b IS NULL`）になる。
