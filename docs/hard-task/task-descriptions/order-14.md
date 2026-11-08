# 不具合報告: Windows を模した偽のファイルシステムで、ドライブ相対パスの `resolve()` が誤ったパスを返す

作業ディレクトリの repository（pyfakefs）にある次の不具合を修正してください。

## 症状

Windows を模した偽のファイルシステムで、`c:test\data.xml` のようにドライブ名の後に `\` を付けない相対パス（ドライブ相対パス）を `pathlib` の `Path.resolve()` で解決すると、期待するパスにならない。

## 再現手順

```python
import os
import pathlib
from pyfakefs.fake_filesystem import OSType
from pyfakefs.fake_filesystem_unittest import Patcher

results = []
with Patcher() as patcher:
    patcher.fs.os = OSType.WINDOWS
    patcher.fs.create_file(r"C:\root\test_data\dummy1.xml")
    os.chdir(r"C:\root")
    results.append(f"cwd {pathlib.Path.cwd()}")
    for text in [r"c:test\test_data\dummy1.xml", r"x:test\test_data\dummy1.xml"]:
        p = pathlib.Path(text)
        results.append(f"{text} is_absolute: {p.is_absolute()}")
        try:
            results.append(f"  resolved: {p.resolve(strict=False)}")
        except Exception as exc:
            results.append(f"  raised {type(exc).__name__}")
print("\n".join(results))
```

## 期待結果

- 現在のドライブ（`C:`）のドライブ相対パス `c:test\test_data\dummy1.xml` は、現在のディレクトリを基準に `C:\root\test\test_data\dummy1.xml` へ解決される（ドライブ名の大文字・小文字の違いは問わない）
- 存在しないドライブ（`x:`）のドライブ相対パスは、例外にならず `x:test\test_data\dummy1.xml` のまま返る

## 実際の結果

標準出力:

```text
cwd C:\root
c:test\test_data\dummy1.xml is_absolute: False
  resolved: c:\est\test_data\dummy1.xml
x:test\test_data\dummy1.xml is_absolute: False
  resolved: x:\est\test_data\dummy1.xml
```

どちらも現在のディレクトリが反映されず、`test` の先頭の `t` が欠けたパスになる。
