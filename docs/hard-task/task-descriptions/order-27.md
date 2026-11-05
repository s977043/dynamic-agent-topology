# 不具合報告: ユニバーサル文字名（\u・\U）を含む文字定数が解析できない

作業ディレクトリの repository（pycparser）にある次の不具合を修正してください。

## 症状

C11 では文字定数の中にユニバーサル文字名（`\u` に 16 進 4 桁、`\U` に 16 進 8 桁）を書ける。しかし、これを含む文字定数を解析すると、接頭辞（なし・`L`・`u8`・`u`・`U`）にかかわらず構文エラーになる。ユニバーサル文字名を含む複数文字の文字定数（例: `'\u00e9a'`）も同じくエラーになる。ユニバーサル文字名を含まない複数文字の文字定数（例: `'ab'`）は解析できる。

## 再現手順

```python
from pycparser import CParser

p = CParser()
for lit in [r"'\u00e9'", r"'\U0001F600'", r"L'\u03A9'", r"u8'\u00e9'", r"u'\u00e9'",
            r"U'\U0001F600'", r"'\u00e9a'", r"'\U0001F6000'", r"'a\u00e9'",
            r"'\u00e9\U0001F600'", r"'\u00e9\u00f1\u03a9\u03b1'", r"'ab'"]:
    try:
        init = p.parse(f"int x = {lit};").ext[0].init
        print(lit, "->", type(init).__name__, init.type)
    except Exception as e:
        print(lit, "-> raised", type(e).__name__)
```

## 期待結果

- ユニバーサル文字名 1 つだけの文字定数は、どの接頭辞でもエラーにならず、他の文字定数と同じく定数として解析される（接頭辞なしの `'\u00e9'` は `'a'` と同じ char 型の定数）
- ユニバーサル文字名は桁数が固定であり、`\u` の後の 4 桁・`\U` の後の 8 桁を超えて続く 16 進数字は別の文字として扱われる。そのため `'\u00e9a'`・`'\U0001F6000'`・`'a\u00e9'`・`'\u00e9\U0001F600'`・`'\u00e9\u00f1\u03a9\u03b1'` は、`'ab'` と同じく複数文字の文字定数（int 型）として解析される
- `'ab'` の結果は今と変わらない

## 実際の結果

標準出力:

```text
'\u00e9' -> raised ParseError
'\U0001F600' -> raised ParseError
L'\u03A9' -> raised ParseError
u8'\u00e9' -> raised ParseError
u'\u00e9' -> raised ParseError
U'\U0001F600' -> raised ParseError
'\u00e9a' -> raised ParseError
'\U0001F6000' -> raised ParseError
'a\u00e9' -> raised ParseError
'\u00e9\U0001F600' -> raised ParseError
'\u00e9\u00f1\u03a9\u03b1' -> raised ParseError
'ab' -> Constant int
```

ユニバーサル文字名を含む 11 個はすべて `ParseError` になる。
