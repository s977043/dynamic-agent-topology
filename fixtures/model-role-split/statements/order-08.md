## 症状

Snowflake の table function `SPLIT_TO_TABLE` が専用の式として扱われません。

## 再現手順

```python
import sqlglot

ast = sqlglot.parse_one("SELECT value FROM TABLE(SPLIT_TO_TABLE('a.b.c', '.'))", read="snowflake")
print(type(ast.args["from_"].this.this))
```

## 期待結果

- `SPLIT_TO_TABLE(<string>, <delimiter>)` を `sqlglot.exp.SplitToTable` として parse し、Snowflake で同じ SQL に戻す
- `SELECT value FROM t, LATERAL SPLIT_TO_TABLE(t.a, '.')` も同じ SQL に戻る
## 実際の結果

`sqlglot.exp.SplitToTable` が存在せず、無名の関数として扱われます。
