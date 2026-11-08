# 不具合報告: Oracle 方言で、物理属性や STORAGE 指定を含む CREATE TABLE 文が通常の文として扱われない

作業ディレクトリの repository（sqlglot）にある次の不具合を修正してください。

## 症状

Oracle 方言で、`CREATE TABLE` の列定義の後（または `AS SELECT` の前）に `PCTFREE 10`、`PCTUSED 40`、`INITRANS 2`、`MAXTRANS 255`、`LOGGING`、`NOLOGGING` や `STORAGE (INITIAL 64K NEXT 1M)` のような指定を書くと、「unsupported syntax」の警告が出て、文全体が解析されないまま扱われる。そのため、別の方言へ変換しても元の文がそのまま出力される。小文字で書いた正しい指定が構文エラーになる一方、中身が空の `STORAGE ()` は構文エラーにならない。

## 再現手順

```python
from sqlglot import parse_one

for sql in ['CREATE TABLE t (id NUMBER) PCTFREE 10 PCTUSED 40 INITRANS 2 MAXTRANS 255 NOLOGGING',
            'CREATE TABLE t (id NUMBER) TABLESPACE ts PCTFREE 10 STORAGE (INITIAL 64K)',
            'create table t (id number) storage (initial 64 k next 1 m) nologging',
            'CREATE TABLE t PCTFREE 10 NOLOGGING AS SELECT 1 AS id FROM dual']:
    try:
        e = parse_one(sql, read="oracle")
    except Exception as exc:
        print("raised", type(exc).__name__, sql)
        continue
    print(type(e).__name__, e.sql("oracle"))
    try:
        print("  postgres:", e.sql("postgres", unsupported_level="RAISE"))
    except Exception as exc:
        print("  postgres raised", type(exc).__name__)

for sql in ['CREATE TABLE t (id NUMBER) STORAGE ()',
            'CREATE TABLE t (id NUMBER) STORAGE (INITIAL 64K UNKNOWN 1)']:
    try:
        print(type(parse_one(sql, read="oracle")).__name__, sql)
    except Exception as exc:
        print("raised", type(exc).__name__, sql)
```

## 期待結果

- 最初の 4 つの文は警告なく、他の `CREATE TABLE` 文と同じように通常の文として扱われる（`AS SELECT` を含む文では、その問い合わせも構造として扱われる）
- Oracle 方言で SQL に戻すと入力と同じ文になる。小文字や数値と単位の間の空白は正規化され、3 つ目は `CREATE TABLE t (id NUMBER) STORAGE (INITIAL 64K NEXT 1M) NOLOGGING` になる
- それらの指定を表せない方言（例: postgres）へ `unsupported_level="RAISE"` で変換すると、未対応であることを示すエラーになる
- 書き方の誤った最後の 2 つの文は、構文エラーとして拒否される

## 実際の結果

標準出力:

```text
Command CREATE TABLE t (id NUMBER) PCTFREE 10 PCTUSED 40 INITRANS 2 MAXTRANS 255 NOLOGGING
  postgres: CREATE TABLE t (id NUMBER) PCTFREE 10 PCTUSED 40 INITRANS 2 MAXTRANS 255 NOLOGGING
Command CREATE TABLE t (id NUMBER) TABLESPACE ts PCTFREE 10 STORAGE (INITIAL 64K)
  postgres: CREATE TABLE t (id NUMBER) TABLESPACE ts PCTFREE 10 STORAGE (INITIAL 64K)
raised ParseError create table t (id number) storage (initial 64 k next 1 m) nologging
Command CREATE TABLE t PCTFREE 10 NOLOGGING AS SELECT 1 AS id FROM dual
  postgres: CREATE TABLE t PCTFREE 10 NOLOGGING AS SELECT 1 AS id FROM dual
Command CREATE TABLE t (id NUMBER) STORAGE ()
raised ParseError CREATE TABLE t (id NUMBER) STORAGE (INITIAL 64K UNKNOWN 1)
```

あわせて、`Command` になった 4 つの文ごとに次の形の警告が出る。

```text
'CREATE TABLE t (id NUMBER) STORAGE ()' contains unsupported syntax. Falling back to parsing as a 'Command'.
```

結果の型は `Command` で、postgres への変換もエラーにならず元の文がそのまま出力される。3 つ目の文は構文エラーになり、`STORAGE ()` は構文エラーにならない。
