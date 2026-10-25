## 症状

Hive / Spark の文字列リテラルの中のバックスラッシュ・エスケープ（`\n`、`\001` などの 8 進、`\U0001F600` などの Unicode）が文字として解釈されず、変換後の SQL に `\` が残ったり、二重になったりします。

## 再現手順

```python
import sqlglot

print(sqlglot.transpile(r"SELECT '\U0001F600'", read="spark", write="spark")[0])
print(sqlglot.transpile("SELECT '\\\n'", read="hive", write="hive")[0])
```

## 期待結果

- Spark: `'\U0001F600'` は `'😀'`。raw 文字列 `r'A\101\z'` は `'\\u0041\\101\\z'`（エスケープを解釈しない）
- Spark 2: `'\U0001F600'` を既定の dialect に変換すると `'U0001F600'`
- Hive: `'\`（改行）`'` は `'\n'`
- Hive: `ROW FORMAT DELIMITED FIELDS TERMINATED BY '\001'` を含む `INSERT OVERWRITE DIRECTORY` の文は、Hive への出力で `'\\001'`（エスケープを保った表記）

## 実際の結果

`'\\U0001F600'` のように `\` が残る・二重になる、または制御文字がそのまま出力に入ります。
