# 不具合報告: 選択肢の式の例外メッセージに、空白の後では最初の選択肢しか出ない

作業ディレクトリの repository（pyparsing）にある次の不具合を修正してください。

## 症状

`a | b`（MatchFirst）や `a ^ b`（Or）のような選択肢の式で、どの選択肢にも一致しないとき、通常は `Expected {x | y}, ...` のようにすべての選択肢を示す例外メッセージになる。ところが、一致しない箇所の前に空白があると、`a | b` のメッセージが `Expected x, ...` のように最初の選択肢だけになる。packrat や左再帰の解析を有効にした場合も含め、空白の有無でメッセージが変わらないことが期待される。

## 再現手順

```python
import pyparsing as pp

x = pp.Regex("x").set_name("x")
y = pp.Regex("y").set_name("y")

for alt in [x | y, x ^ y]:
    expr = "let" + alt
    for text in ["letz", "let z"]:
        try:
            expr.parse_string(text)
        except pp.ParseException as exc:
            print(repr(text), "->", exc)
```

## 期待結果

- 空白の有無にかかわらず、`x | y` では `Expected {x | y}, found 'z'`、`x ^ y` では `Expected {x ^ y}, found 'z'` のように、すべての選択肢を示すメッセージになる
- 例外の位置（char・line・col）はこれまでどおり、一致しなかった文字の位置を示す

## 実際の結果

```text
'letz' -> Expected {x | y}, found 'z'  (at char 3), (line:1, col:4)
'let z' -> Expected x, found 'z'  (at char 4), (line:1, col:5)
'letz' -> Expected {x ^ y}, found 'z'  (at char 3), (line:1, col:4)
'let z' -> Expected {x ^ y}, found 'z'  (at char 4), (line:1, col:5)
```

`x | y` で入力に空白がある場合だけ、メッセージが最初の選択肢 `x` だけになる。この再現コード（packrat なし）では `x ^ y` のメッセージは空白があってもすべての選択肢を示した。
