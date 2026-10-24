## 症状

CONTEXTJ の規則に反するラベル（前に Virama がない ZWNJ / ZWJ を含むラベル）を検査すると、`InvalidCodepointContext` ではなく、一般の `IDNAError`（「Unknown codepoint adjacent to joiner」）が返ります。

## 再現手順

```python
import idna

idna.check_label("a‌a")
```

## 期待結果

- `idna.InvalidCodepointContext` が発生し、メッセージに `not allowed at position 2` を含む。ZWJ（`"a‍a"`）でも同じ。`idna.encode` でも `InvalidCodepointContext` になる
- 正しい文脈（`"a्‍a"`、`"a्‌a"`）は従来どおり受理される
- 隣の codepoint が unicodedata で引けない場合は、従来どおり `InvalidCodepointContext` ではない `IDNAError`（「Unknown codepoint adjacent to joiner」）になる

## 実際の結果

`idna.core.IDNAError: Unknown codepoint adjacent to joiner U+200C at position 2 in 'a‌a'`
