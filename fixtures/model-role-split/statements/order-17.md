## 症状

`ALTER TABLE ... DROP COLUMN col1, col2` のように、2 つ目以降の列で `DROP` を省略した書き方を、Snowflake と T-SQL で parse できません。文全体が汎用の `Command` に落ちます。

## 再現手順

```python
import sqlglot
from sqlglot import exp

ast = sqlglot.parse_one("ALTER TABLE tbl DROP COLUMN col1, col2", read="snowflake")
print(type(ast))
```

## 期待結果

- Snowflake / T-SQL: `exp.Alter` として parse し、その中の `exp.Drop` は 1 つで、`kind` は `"COLUMN"`、`tables` の名前は `["col1", "col2"]`。同じ SQL に戻る
- 既定の dialect では、従来どおり列ごとに `DROP` が必要
- MySQL: `ALTER TABLE t DROP PRIMARY KEY` の action は `exp.DropPrimaryKey`。`ALTER TABLE t DROP COLUMN a, ALGORITHM=INPLACE` は同じ SQL に戻る

## 実際の結果

`Command(this=ALTER, expression=TABLE tbl DROP COLUMN col1, col2)` になります。
