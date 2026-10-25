## 症状

ClickHouse で、引用符付きの識別子の中のバックスラッシュが、生成時にエスケープされません。

## 再現手順

```python
import sqlglot

print(sqlglot.transpile(r'SELECT "a\\"', read="clickhouse", write="clickhouse")[0])
```

## 期待結果

- `SELECT "a\\"`（入力と同じ）。`SELECT "a\\""b"` も入力と同じ
- `` SELECT `a\\b` `` は `SELECT "a\\b"`
- PostgreSQL の `SELECT "a\b"` は ClickHouse で `SELECT "a\\b"`。逆に ClickHouse の `SELECT "a\\b"` は PostgreSQL で `SELECT "a\b"`

## 実際の結果

`SELECT "a\"`（バックスラッシュが 1 つになり、識別子が壊れる）
