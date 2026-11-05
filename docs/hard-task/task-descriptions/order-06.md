# 不具合報告: 先頭に `/` の付いたパスと付かないパスを一緒に照合すると、一致したパスの一部が返らない

作業ディレクトリの repository（python-pathspec）にある次の不具合を修正してください。

## 症状

`PathSpec.match_files()` に、先頭に `/` の付いたパス（例: `/foo/a.py`）と先頭に `/` の付かないパス（例: `foo/a.py`）を一緒に渡すと、パターンに一致するはずのパスの一部が結果に含まれない。

## 再現手順

```python
import pathspec

files = ['/a.py', '/foo/a.py', '/x/a.py', '/x/foo/a.py',
         'a.py', 'foo/a.py', 'x/a.py', 'x/foo/a.py']
for pattern in ['foo', '/foo']:
    spec = pathspec.PathSpec.from_lines('gitwildmatch', [pattern])
    print(pattern, sorted(spec.match_files(files)))
```

## 期待結果

- パターン `foo` では `/foo/a.py`、`/x/foo/a.py`、`foo/a.py`、`x/foo/a.py` の 4 件が返る
- パターン `/foo` では `/foo/a.py` と `foo/a.py` の 2 件が返る
- 渡したパスは、渡したときの表記のまま返る

## 実際の結果

標準出力:

```text
foo ['/x/foo/a.py', 'foo/a.py', 'x/foo/a.py']
/foo ['foo/a.py']
```

どちらのパターンでも `/foo/a.py` が結果に含まれない。
