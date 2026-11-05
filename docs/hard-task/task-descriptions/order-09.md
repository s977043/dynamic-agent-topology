# 不具合報告: 偽のファイルシステムで `os.path.sameopenfile()` が正しい結果を返さない

作業ディレクトリの repository（pyfakefs）にある次の不具合を修正してください。

## 症状

偽のファイルシステム上で開いたファイルのファイル記述子を `os.path.sameopenfile()` に渡すと、2 つの記述子が同じファイルを指しているかどうかが判定されず、開いている記述子でも例外になる。

## 再現手順

```python
from pyfakefs import fake_filesystem, fake_open, fake_os

fs = fake_filesystem.FakeFilesystem()
fs.create_file("/foo/bar")
fs.create_file("/foo/baz")
fake_os_module = fake_os.FakeOsModule(fs)
fake_path = fake_os_module.path
open_fake = fake_open.FakeFileOpen(fs)

with open_fake("/foo/bar") as first, open_fake("/foo/bar") as second, open_fake("/foo/baz") as other:
    fd1, fd2, fd3 = first.fileno(), second.fileno(), other.fileno()
    for label, a, b in [("same file", fd1, fd2), ("same fd", fd1, fd1), ("other file", fd1, fd3)]:
        try:
            print(label, fake_path.sameopenfile(a, b))
        except Exception as exc:
            print(label, "raised", type(exc).__name__)

try:
    print("closed", fake_path.sameopenfile(fd1, fd2))
except OSError as exc:
    print("closed raised OSError", exc.errno)
```

## 期待結果

- 同じ偽ファイルを開いた 2 つの記述子では `True`、同じ記述子どうしでも `True`
- 別の偽ファイルの記述子とでは `False`
- 閉じた後の記述子を渡すと、`errno` が `EBADF`（9）の `OSError` になる

## 実際の結果

標準出力:

```text
same file raised OSError
same fd raised OSError
other file raised OSError
closed raised OSError 9
```

ファイルを開いている間の 3 つの呼び出しも、すべて `OSError` になる。
