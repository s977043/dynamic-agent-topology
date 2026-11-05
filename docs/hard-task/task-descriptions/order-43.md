# 不具合報告: REGEXP_COUNT を ClickHouse 方言へ変換すると ClickHouse にない関数が出力される

作業ディレクトリの repository（sqlglot）にある次の不具合を修正してください。

## 症状

Snowflake などの `REGEXP_COUNT(文字列, パターン[, 開始位置[, フラグ]])` を ClickHouse 方言へ変換すると、`REGEXP_COUNT(...)` がそのまま出力される。ClickHouse には `REGEXP_COUNT` 関数がなく、正規表現の一致回数は `countMatches(文字列, パターン)` で数えるため、出力された SQL は ClickHouse で実行できない。逆に ClickHouse の `countMatches(...)` を Snowflake 方言へ変換すると `COUNTMATCHES(...)` がそのまま出力され、Snowflake で実行できない。

## 再現手順

```python
import sqlglot

for sql in ["SELECT REGEXP_COUNT(name, 'o')",
            "SELECT REGEXP_COUNT(name, 'o.e', 2, 'i')"]:
    print(sqlglot.transpile(sql, read="snowflake", write="clickhouse")[0])

print(sqlglot.transpile("SELECT countMatches(name, 'o')", read="clickhouse", write="snowflake")[0])
```

## 期待結果

- Snowflake の `REGEXP_COUNT(name, 'o')` は ClickHouse 方言で `countMatches(name, 'o')` になり、ClickHouse の `countMatches(name, 'o')` は Snowflake 方言で `REGEXP_COUNT(name, 'o')` になる。ClickHouse 方言どうしでは `countMatches(...)` のまま戻る
- 開始位置を指定した場合は、文字列のその位置（バイトではなく文字単位で数えた位置）から後ろだけを数える ClickHouse の式になる
- フラグを指定した場合は、ClickHouse の正規表現で同じ意味になるようにする。`i`（大文字小文字を区別しない）、`m`、`s` は反映し、`c`（区別する、既定）と `i` が両方あるときは後に書かれた方が優先される。表せないフラグは未対応として扱う

## 実際の結果

標準出力:

```text
SELECT REGEXP_COUNT(name, 'o')
SELECT REGEXP_COUNT(name, 'o.e', 2, 'i')
SELECT COUNTMATCHES(name, 'o')
```

ClickHouse への変換で `REGEXP_COUNT` がそのまま出力され、Snowflake への変換で `COUNTMATCHES` がそのまま出力される。
