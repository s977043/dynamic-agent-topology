# 不具合報告: Oracle 方言で、テーブルのパーティションを指定した SELECT・INSERT が正しく扱われない

作業ディレクトリの repository（sqlglot）にある次の不具合を修正してください。

## 症状

Oracle 方言では、テーブル名の直後に `PARTITION(<名前>)` または `SUBPARTITION(<名前>)` を書いて、読み書きするパーティションを指定できる。この指定を含む `SELECT` や `INSERT` を解析して Oracle 方言の SQL に戻すと、入力と同じ文にならない、または解析が失敗する。

## 再現手順

```python
from sqlglot import parse_one

for sql in ['SELECT * FROM "SH"."SALES" PARTITION(p1) s',
            'SELECT * FROM "SH"."SALES" SUBPARTITION("P1") s',
            'INSERT INTO sales PARTITION(p1) VALUES (1)',
            'INSERT INTO sales SUBPARTITION(p1) s (col1) VALUES (1)']:
    try:
        e = parse_one(sql, read="oracle")
        print("OK ", e.sql("oracle"))
    except Exception as exc:
        print("ERR", type(exc).__name__)
```

## 期待結果

- 4 つの文はすべてエラーなく解析できる
- Oracle 方言で SQL に戻すと、入力と同じ文になる（`PARTITION` と `SUBPARTITION` の区別、パーティション名、別名、列の並びが保たれる）

## 実際の結果

標準出力:

```text
ERR ParseError
ERR ParseError
OK  INSERT INTO sales PARTITION (p1) VALUES (1)
ERR ParseError
```

別名の付いた 3 件は解析エラーになり、別名のない `INSERT` は解析できるが、SQL に戻すと `PARTITION` と `(p1)` の間に空白が入り、入力と同じ文にならない。
