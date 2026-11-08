# 不具合報告: Oracle 方言で一部の q'...' 形式の文字列リテラルと nq'...' 形式が読めない

作業ディレクトリの repository（sqlglot）にある次の不具合を修正してください。

## 症状

Oracle の代替引用符の文字列リテラル（`q'<区切り文字>...<区切り文字>'`）は、`q'[it's]'` のような一部の区切り文字では読めるが、`]` や英字を区切り文字にした形はエラーになる。また、national 文字列の代替引用符形式（`nq'...'`、`NQ'...'` など）は、区切り文字にかかわらずエラーになる。

## 再現手順

```python
import sqlglot

for sql in ["SELECT q'[it's]' FROM dual",
            "SELECT q']it's]' FROM dual",
            "SELECT q'ait'sa' FROM dual",
            "SELECT nq'[it's]' FROM dual",
            "SELECT NQ'!it's!' FROM dual",
            "SELECT TRIM(nq'[both]')"]:
    try:
        print(repr(sql), "->", repr(sqlglot.transpile(sql, read="oracle", write="oracle")[0]))
    except Exception as e:
        print(repr(sql), "-> raised", type(e).__name__)
```

## 期待結果

- Oracle が代替引用符の区切り文字として認める文字（`]`・`}`・`)`・`>`・英字・数字なども含む）であれば、`q'...'` は今の `q'[it's]'` と同じく通常の文字列として読める（例: `SELECT 'it''s' FROM dual`）
- `nq'...'`（`n`・`q` の大文字・小文字の組み合わせを問わない）は national 文字列として読め、Oracle 方言で SQL に戻すと `N'...'` の形になる（例: `SELECT N'it''s' FROM dual`、`SELECT TRIM(N'both')`）

## 実際の結果

標準出力:

```text
"SELECT q'[it's]' FROM dual" -> "SELECT 'it''s' FROM dual"
"SELECT q']it's]' FROM dual" -> raised TokenError
"SELECT q'ait'sa' FROM dual" -> raised TokenError
"SELECT nq'[it's]' FROM dual" -> raised TokenError
"SELECT NQ'!it's!' FROM dual" -> raised TokenError
"SELECT TRIM(nq'[both]')" -> raised ParseError
```

`q'[it's]'` 以外の 5 つはいずれも例外になる。
