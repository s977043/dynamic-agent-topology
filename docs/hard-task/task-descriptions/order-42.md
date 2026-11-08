# 不具合報告: static_file() が圧縮ファイルに Content-Encoding を付けて返す

作業ディレクトリの repository（bottle）にある次の不具合を修正してください。

## 症状

`static_file()` で `backup.tar.gz` のような圧縮ファイルを返すと、`Content-Type` が圧縮前の形式（`application/x-tar`）になり、`Content-Encoding: gzip` が付く。ブラウザはこれを「転送のために圧縮された tar」と解釈して自動で展開するため、利用者が受け取るファイルが元の `.gz` ファイルと違うものになる。`.bz2` などの他の圧縮形式でも同様に `Content-Encoding` が付く。

## 再現手順

```python
import os
import tempfile

from bottle import static_file

root = tempfile.mkdtemp()
for name in ["backup.tar.gz", "data.csv.bz2", "notes.txt"]:
    with open(os.path.join(root, name), "wb") as f:
        f.write(b"x")
    res = static_file(name, root=root)
    print(name, "| Content-Type:", res.headers.get("Content-Type"),
          "| Content-Encoding:", res.headers.get("Content-Encoding"))
```

## 期待結果

- 圧縮ファイルはそのままのファイルとして返され、`Content-Encoding` は付かない
- `.gz` のファイル（例: `backup.tar.gz`、`report.txt.gz`）の `Content-Type` は `application/gzip` になる。他の圧縮形式も、圧縮前の形式ではなく圧縮ファイルとしての型になる
- 圧縮されていないファイル（例: `notes.txt`）の `Content-Type` と charset の扱いは変わらない

## 実際の結果

```text
backup.tar.gz | Content-Type: application/x-tar | Content-Encoding: gzip
data.csv.bz2 | Content-Type: text/csv; charset=UTF-8 | Content-Encoding: bzip2
notes.txt | Content-Type: text/plain; charset=UTF-8 | Content-Encoding: None
```

圧縮ファイルに圧縮前の形式の `Content-Type` と `Content-Encoding` が付く。
