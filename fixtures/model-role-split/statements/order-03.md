## 症状

`INSERT INTO <table> AS <alias> (<columns>) ...` の形で、対象テーブルの alias の直後に書いた列リストが、INSERT の列リストではなく alias の列として解釈されます。

## 再現手順

```python
import sqlglot

print(sqlglot.transpile("INSERT INTO foo AS f (x, y) VALUES (1, 2)", read="sqlite", write="sqlite")[0])
print(sqlglot.transpile(
    "INSERT INTO newtable AS t(a, b, c) VALUES (1, 2, 3) ON CONFLICT(c) DO UPDATE SET a = t.a + 1 WHERE t.a < 1",
    read="postgres", write="postgres")[0])
```

## 期待結果

- SQLite: `INSERT INTO foo AS f (x, y) VALUES (1, 2)`
- PostgreSQL: `INSERT INTO newtable AS t (a, b, c) VALUES (1, 2, 3) ON CONFLICT(c) DO UPDATE SET a = t.a + 1 WHERE t.a < 1`

## 実際の結果

- SQLite: `INSERT INTO foo AS f VALUES (1, 2)`（列リストが消える）
- PostgreSQL: `INSERT INTO newtable AS t(a, b, c) VALUES ...`
