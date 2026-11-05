# 不具合報告: Located が報告する開始位置に、一致の前の空白が含まれることがある

作業ディレクトリの repository（pyparsing）にある次の不具合を修正してください。

## 症状

`pp.Located(式)` は一致した範囲の開始位置 `locn_start` と終了位置 `locn_end` を返す。単独の `Keyword` を包んだ場合は先頭の空白を飛ばした位置が返るが、`abc | abc` のような選択の式を包むと、入力の先頭の空白まで一致範囲に含めた位置（`locn_start=0`）が返る。packrat を有効にしても無効にしても同じ結果になる。

## 再現手順

```python
import pyparsing as pp

for packrat in (False, True):
    if packrat:
        pp.ParserElement.enable_packrat()
    print("packrat:", packrat)
    abc = pp.Keyword("abc")
    for label, expr, text in [
        ("Located(abc)", pp.Located(abc), "   abc"),
        ("Located(abc | abc)", pp.Located(abc | abc), "   abc"),
        ("Located(Literal('ID') + Word)", pp.Located(pp.Literal("ID") + pp.Word(pp.alphanums)), "   ID PARI12345678"),
        ("Located(Word(' abc').leave_whitespace())", pp.Located(pp.Word(" abc").leave_whitespace()), "   abc"),
    ]:
        r = expr.parse_string(text)
        print(" ", label, r.locn_start, r.locn_end, repr(text[r.locn_start:r.locn_end]))
```

## 期待結果

- 包んだ式の種類（単独の式・選択・連結）にかかわらず、`locn_start` は空白を飛ばした実際の一致の開始位置になる。`Located(abc | abc)` では `3 6 'abc'` になる
- `Located(abc)` と `Located(Literal('ID') + Word)` の結果は今と同じ
- `leave_whitespace()` で空白を残すよう指定した式では、今と同じく先頭の空白も一致範囲に含まれる（`locn_start` は 0）
- packrat の有無で結果は変わらない

## 実際の結果

標準出力:

```text
packrat: False
  Located(abc) 3 6 'abc'
  Located(abc | abc) 0 6 '   abc'
  Located(Literal('ID') + Word) 3 18 'ID PARI12345678'
  Located(Word(' abc').leave_whitespace()) 0 6 '   abc'
packrat: True
  Located(abc) 3 6 'abc'
  Located(abc | abc) 0 6 '   abc'
  Located(Literal('ID') + Word) 3 18 'ID PARI12345678'
  Located(Word(' abc').leave_whitespace()) 0 6 '   abc'
```

`Located(abc | abc)` だけ、先頭の空白 3 文字を含む `0 6 '   abc'` になる。
