# 不具合報告: Teradata のウィンドウ集約を別の方言へ変換すると集計範囲が変わる

作業ディレクトリの repository（sqlglot）にある次の不具合を修正してください。

## 症状

Teradata では、`ORDER BY` を持ち `ROWS` 句を持たないウィンドウ集約（例: `SUM(x) OVER (PARTITION BY p ORDER BY d)`）は、パーティション全体を集計範囲とする。これは ANSI SQL の既定（先頭から現在行までの累積）と異なる。ところが Teradata 方言から DuckDB などへ変換すると、集計範囲を指定しないまま出力されるため、変換先では累積の集計として計算されてしまう。

## 再現手順

```python
import sqlglot

for sql in ["SELECT AVG(amount) OVER (PARTITION BY region ORDER BY day) FROM sales",
            "SELECT MAX(amount) OVER (ORDER BY day) FROM sales",
            "SELECT DENSE_RANK() OVER (ORDER BY day) FROM sales"]:
    for target in ["teradata", "duckdb"]:
        print(target, sqlglot.transpile(sql, read="teradata", write=target)[0])
```

## 期待結果

- Teradata 方言の、`ORDER BY` を持ち `ROWS` 句を持たないウィンドウ集約（`SUM`、`AVG`、`MAX`、`COUNT(*)` など）を別の方言（DuckDB、Snowflake など）へ変換すると、パーティション全体を集計範囲とする指定 `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` が付き、Teradata と同じ結果を計算する SQL になる（例: `AVG(amount) OVER (PARTITION BY region ORDER BY day NULLS FIRST ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)`）
- Teradata 方言へ戻すときは、入力と同じ文（集計範囲の指定なし）になる
- `ORDER BY` を持たないウィンドウ集約は変わらない
- 集約でないウィンドウ関数（`RANK`、`DENSE_RANK`、`ROW_NUMBER`、`LAG` など）と、`FIRST_VALUE` には集計範囲の指定を付けない

## 実際の結果

標準出力:

```text
teradata SELECT AVG(amount) OVER (PARTITION BY region ORDER BY day) FROM sales
duckdb SELECT AVG(amount) OVER (PARTITION BY region ORDER BY day NULLS FIRST) FROM sales
teradata SELECT MAX(amount) OVER (ORDER BY day) FROM sales
duckdb SELECT MAX(amount) OVER (ORDER BY day NULLS FIRST) FROM sales
teradata SELECT DENSE_RANK() OVER (ORDER BY day) FROM sales
duckdb SELECT DENSE_RANK() OVER (ORDER BY day NULLS FIRST) FROM sales
```

DuckDB への変換で集計範囲の指定が付かず、変換先では累積の集計になる。
