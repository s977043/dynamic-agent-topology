# 不具合報告: Oracle の CREATE TABLE に TABLESPACE を付けると構文として解析されない

作業ディレクトリの repository（sqlglot）にある次の不具合を修正してください。

## 症状

Oracle 方言で、列定義の後に `TABLESPACE <名前>` を付けた `CREATE TABLE` を解析すると、「unsupported syntax」の警告が出て、文全体が解析されないまま扱われる。そのため別の方言へ変換しても、元の文がそのまま出力される。

## 再現手順

```python
from sqlglot import parse_one

for sql in ['CREATE TABLE t (id NUMBER) TABLESPACE ts',
            'CREATE TABLE t (id NUMBER) TABLESPACE "Mixed Ts"']:
    e = parse_one(sql, read="oracle")
    print(type(e).__name__, e.sql("oracle"))
    print(e.sql("postgres", unsupported_level="RAISE"))
```

## 期待結果

- 結果は `CREATE TABLE` の式として解析され、テーブル名と列定義（`id NUMBER`）が構造として取り出せる
- Oracle 方言で SQL に戻すと、入力と同じ文になる（引用符付きの名前も保たれる）
- TABLESPACE を表せない方言（例: postgres）へ `unsupported_level="RAISE"` で変換すると、未対応であることを示すエラーになる

## 実際の結果

標準出力:

```text
Command CREATE TABLE t (id NUMBER) TABLESPACE ts
CREATE TABLE t (id NUMBER) TABLESPACE ts
Command CREATE TABLE t (id NUMBER) TABLESPACE "Mixed Ts"
CREATE TABLE t (id NUMBER) TABLESPACE "Mixed Ts"
```

あわせて、入力ごとに次の警告が出る。

```text
'CREATE TABLE t (id NUMBER) TABLESPACE ts' contains unsupported syntax. Falling back to parsing as a 'Command'.
```

結果の型は `Command` で、postgres への変換もエラーにならず元の文がそのまま出力される。
