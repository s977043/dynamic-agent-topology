## 症状

`Regex` を要素に持つ `Each`（`&`）が、入力に 1 回しか現れない要素を 2 回分 parse します。

## 再現手順

```python
import pyparsing as pp

print(pp.Each([pp.Regex(r"[a-z]+")]).parseString("abc def").asList())
```

## 期待結果

`['abc']`。`pp.ParseExpression` のどのサブクラス（`And`・`Or`・`MatchFirst`・`Each`）に `Regex(r"[a-z]+")` または `Regex(r"[a-z]*")` を 1 つ渡しても同じ。`MatchFirst([expr, expr])` と `Or([expr, expr])` も `['abc']`。packrat の有効・無効によらない

## 実際の結果

`Each` では `['abc', 'def']` になります。
