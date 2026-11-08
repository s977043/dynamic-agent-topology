# 不具合報告: StarRocks 方言の map{...} が map として扱われない

作業ディレクトリの repository（sqlglot）にある次の不具合を修正してください。

## 症状

StarRocks 方言で `map{key:value, ...}` の形の map リテラルを解析すると、map ではなく struct として扱われる。StarRocks 方言で SQL に戻すと `STRUCT(...)` になり、キーが列名に置き換わる。そのため `map{...}[key]` のような添字アクセスも StarRocks が受け付けない SQL になる。DuckDB など別の方言へ変換しても map にならない。

あわせて、DuckDB 方言の `MAP {t.k: t.v}` のように、キーに列参照を書いた map リテラルでは、キーが文字列リテラルに置き換わる。

## 再現手順

```python
import sqlglot

for sql in ["SELECT MAP{1:1, 2:2} AS numbers",
            "SELECT map{1:'apple', 2:'orange'}[1] AS fruit"]:
    print(sqlglot.transpile(sql, read="starrocks", write="starrocks")[0])
    print(sqlglot.transpile(sql, read="starrocks", write="duckdb")[0])

sql = "SELECT MAP {t.k: t.v} FROM (SELECT 'a' AS k, 10 AS v) AS t"
print(sqlglot.transpile(sql, read="duckdb", write="duckdb")[0])
```

## 期待結果

- StarRocks 方言の `map{...}` は map として扱われ、StarRocks 方言で SQL に戻すと `MAP{1:1, 2:2}` のように `MAP{...}` の形で出力される（入れ子の map、空の `map{}`、値の `NULL`、添字アクセスも同様）
- DuckDB 方言へ変換すると DuckDB の map リテラル（例: `MAP {1: 1, 2: 2}`）になり、逆に DuckDB の map リテラルを StarRocks 方言へ変換すると `MAP{...}` になる
- `map` を列名などの識別子として使う文（例: `SELECT map, t.map, map[1] FROM t`）はこれまでどおり識別子として扱われる
- DuckDB 方言の `MAP {t.k: t.v}` は、キーの列参照を保ったまま同じ文に戻る

## 実際の結果

標準出力:

```text
SELECT STRUCT(1 AS `1`, 2 AS `2`) AS numbers
SELECT {'1': 1, '2': 2} AS numbers
SELECT STRUCT('apple' AS `1`, 'orange' AS `2`)[1] AS fruit
SELECT {'1': 'apple', '2': 'orange'}[1] AS fruit
SELECT MAP {'k': t.v} FROM (SELECT 'a' AS k, 10 AS v) AS t
```

StarRocks の map リテラルは struct として出力され、DuckDB の map リテラルではキーの `t.k` が `'k'` に置き換わる。
