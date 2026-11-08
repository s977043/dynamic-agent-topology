# 不具合報告: DuckDB の ARRAY_SLICE を他の方言へ変換すると取り出す範囲が変わる

作業ディレクトリの repository（sqlglot）にある次の不具合を修正してください。

## 症状

DuckDB 方言の `ARRAY_SLICE(配列, 開始, 終了)` を spark・presto などの方言へ変換すると、引数が同じ値のまま `SLICE(...)` として出力される。変換先の `SLICE` では引数の意味が DuckDB の `ARRAY_SLICE` と異なるため、変換後の SQL は元の SQL と違う範囲の要素を返す。たとえば DuckDB で `ARRAY_SLICE([1, 2, 3, 4], 2, 3)` は `[2, 3]` を返すが、変換後の `SLICE(ARRAY(1, 2, 3, 4), 2, 3)` は Spark では `[2, 3, 4]` を返す。

## 再現手順

```python
import sqlglot

for sql in ["SELECT ARRAY_SLICE([1, 2, 3, 4], 2, 3)",
            "SELECT ARRAY_SLICE(x, 0, 2)",
            "SELECT ARRAY_SLICE(x, 3, 2)"]:
    for dialect in ["spark", "presto"]:
        print(dialect, sqlglot.transpile(sql, read="duckdb", write=dialect)[0])
```

## 期待結果

- 変換後の SQL は、変換先の方言で評価したときに、DuckDB で元の SQL を評価したときと同じ範囲の要素を返す
- 開始位置が 0 の場合や、終了位置が開始位置より前の場合（DuckDB では空の配列になる）も、変換先で同じ結果になる
- DuckDB から DuckDB への変換では、入力と同じ SQL が出力される

## 実際の結果

標準出力:

```text
spark SELECT SLICE(ARRAY(1, 2, 3, 4), 2, 3)
presto SELECT SLICE(ARRAY[1, 2, 3, 4], 2, 3)
spark SELECT SLICE(x, 0, 2)
presto SELECT SLICE(x, 0, 2)
spark SELECT SLICE(x, 3, 2)
presto SELECT SLICE(x, 3, 2)
```

どの入力でも、DuckDB の引数がそのまま `SLICE` の引数として出力される。
