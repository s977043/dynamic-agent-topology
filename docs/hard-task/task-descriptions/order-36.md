# 不具合報告: gitignore 形式のパターン先頭のエスケープした * がワイルドカードとして扱われる

作業ディレクトリの repository（pathspec）にある次の不具合を修正してください。

## 症状

`gitwildmatch`（.gitignore 形式）のパターンで、先頭の `*` を `\*` とエスケープしても、文字としての `*` ではなくワイルドカードとして扱われる。そのため `\*notes.txt` が `mynotes.txt` や `notes.txt` にも一致する。パターンの途中の `\*`（例: `foo\*.txt`）は正しく文字として扱われる。

## 再現手順

```python
import pathspec

files = ["*notes.txt", "mynotes.txt", "notes.txt", "dir/*notes.txt"]
for line in ["\\*notes.txt", "foo\\*.txt"]:
    spec = pathspec.PathSpec.from_lines("gitwildmatch", [line])
    print(repr(line), sorted(spec.match_files(files + ["foo*.txt", "foobar.txt"])))
```

## 期待結果

- `\*notes.txt` は名前が文字どおり `*notes.txt` のファイルだけに一致する（この入力では `*notes.txt` と `dir/*notes.txt`）。`mynotes.txt` と `notes.txt` には一致しない
- `foo\*.txt` はこれまでどおり `foo*.txt` だけに一致する
- 先頭の `\!` や `\#` のような他のエスケープも、文字として扱われる

## 実際の結果

```text
'\\*notes.txt' ['*notes.txt', 'dir/*notes.txt', 'mynotes.txt', 'notes.txt']
'foo\\*.txt' ['foo*.txt']
```

先頭の `\*` がワイルドカードとして扱われ、`mynotes.txt` と `notes.txt` にも一致する。
