## 症状

`sys.tracebacklimit` を小さい値にした状態で、pyfakefs の偽のファイルシステム上のファイルを `open()` すると、`IndexError` で落ちます。

## 再現手順

pyfakefs の `fake_filesystem_unittest.TestCase`（`setUpPyfakefs()` 済み）の中で、次を実行します。

```python
import sys

sys.tracebacklimit = 2
with open("/foo", "w") as f:
    f.write("test")
```

## 期待結果

ファイルが作られ、例外は出ない。テスト後に `sys.tracebacklimit` を元に戻したとき、他のテストに影響しない

## 実際の結果

`IndexError: list index out of range`
