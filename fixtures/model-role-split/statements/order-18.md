## 症状

MySQL で、キーワードと同じ名前の index や列を `DROP` する文を正しく parse できません。

## 再現手順

```python
import sqlglot

sqlglot.parse_one("DROP INDEX concurrently ON t", read="mysql")
```

## 期待結果

- `DROP INDEX concurrently ON t` は同じ SQL に戻る
- `ALTER TABLE t DROP INDEX concurrently` の action は `exp.Drop` で、`tables[0].name` が `"concurrently"`、`args["concurrently"]` が `False`
- `ALTER TABLE t DROP temporary` は `ALTER TABLE t DROP COLUMN temporary`、`ALTER TABLE t DROP iceberg` は `ALTER TABLE t DROP COLUMN iceberg`

## 実際の結果

`ParseError: Expected table name but got <Token token_type: TokenType.ON ...>`
