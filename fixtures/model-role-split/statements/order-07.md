## 症状

Snowflake の stage 一覧コマンド `LIST`（別名 `LS`）を parse できません。

## 再現手順

```python
import sqlglot

sqlglot.parse_one("LIST @~", read="snowflake")
sqlglot.parse_one("LIST @named_stage/path1 PATTERN = '.*data_0.*'", read="snowflake")
```

## 期待結果

- `LIST <location>` を `sqlglot.exp.ListStage` の式として parse する。`this` は `exp.var("<location>")`、`pattern` は文字列リテラル（省略可）。location の例: `@%table1`、`@schema1.%table1`、`@db1.schema1.%table1`、`@named_stage`、`@~`、`@named_stage/path1`、`@~/path1`、`@"my_DB"."schEMA1"."MYstage"/CaseSensitivePath`、`'@"my stage"/my path'`、`@my_repo/branches/main/`
- 生成は `LIST <location>`、pattern があれば `LIST <location> PATTERN = '<pattern>'`（入力の `pattern='...'` も正規化する）
- `LS @~` は `LIST @~` として扱う
- `LIST @stage PATTERN`、`LIST @stage PATTERN '.*'`、`LIST @stage PATTERN =`、`LIST @stage PATTERN = 123` は `ParseError`
- `SELECT list, ls FROM list` や `SELECT x AS list, y AS ls FROM t` のような識別子としての `list` / `ls` は、従来どおり SELECT として扱う

## 実際の結果

`ParseError` になります。
