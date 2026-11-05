# 不具合報告: PathSpec.match_file がどのパターンにも当たらないファイルで真偽値を返さない

作業ディレクトリの repository（python-pathspec）にある次の不具合を修正してください。

## 症状

`PathSpec.match_file()` は、ファイルが含まれるかどうかを真偽値で返す。しかし、どのパターンにも当たらないファイルを渡すと `False` ではなく `None` が返る。

## 再現手順

```python
from pathspec import PathSpec

spec = PathSpec.from_lines("gitwildmatch", ["*.txt", "!test/"])
for path in ["include.txt", "test/exclude.txt", "unmatch.bin"]:
    print(path, repr(spec.match_file(path)))
```

## 期待結果

- `include.txt` は `True`、`test/exclude.txt` は `False` で、今と同じ
- どのパターンにも当たらない `unmatch.bin` は `False` になる（戻り値は常に `True` か `False`）

## 実際の結果

標準出力:

```text
include.txt True
test/exclude.txt False
unmatch.bin None
```

どのパターンにも当たらないファイルで `None` が返る。
