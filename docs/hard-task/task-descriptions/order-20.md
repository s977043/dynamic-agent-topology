# 不具合報告: 不正な JSON を読んだときのエラーの内容が実装によって食い違う

作業ディレクトリの repository（simplejson）にある次の不具合を修正してください。

## 症状

simplejson には C 拡張を使う実装と Python だけの実装があり、不正な JSON に対して出す `JSONDecodeError` の内容は両者で同じになるべきだが、Python だけの実装（C 拡張をビルドしていない状態）では次の 2 つが食い違う。

- `{` だけの入力に対するエラーメッセージが、閉じ括弧 `}` も受け付けられることを示していない
- 文字列の途中に制御文字がある入力（例: `"` の直後に `\x18`）で、エラーの位置 `pos` が制御文字の位置より 1 つ後ろを指す

## 再現手順

C 拡張をビルドしていない checkout で実行する。

```python
import simplejson

for data in ['{', '"\x18d', '[,']:
    try:
        simplejson.loads(data)
    except simplejson.JSONDecodeError as e:
        print(repr(data), repr(e.msg), e.pos)
```

## 期待結果

- `{` に対するメッセージは、二重引用符で囲んだプロパティ名か `}` のどちらかを期待していることを示し、C 拡張を使う実装のメッセージと一致する
- `'"\x18d'` に対するエラーの `pos` は、制御文字の位置である 1 になる
- `[,` のように現在も正しい入力のメッセージと位置は変わらない

## 実際の結果

標準出力:

```text
'{' 'Expecting property name enclosed in double quotes' 1
'"\x18d' 'Invalid control character %r at' 2
'[,' 'Expecting value' 1
```

`{` のメッセージには `}` への言及がなく、制御文字のエラー位置は 2 になる。
