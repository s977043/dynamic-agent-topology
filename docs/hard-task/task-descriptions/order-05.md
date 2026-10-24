# 不具合報告: _Alignas と _Atomic(...) を含む宣言を C に戻すと内容が変わる

作業ディレクトリの repository（pycparser）にある次の不具合を修正してください。

## 症状

C のソースを解析し、その AST を C のコードに戻すと、`_Alignas` や `_Atomic(型)` を含む宣言で次のことが起きる。

- `_Alignas` を複数書いた宣言で、2 つ目以降が消える
- `_Atomic(型)` の外側に書いた修飾子（`const` など）が消える
- `_Atomic(型)` で複数の変数を宣言すると、2 つ目以降の変数名が 1 つ目の名前になる

## 再現手順

```python
from pycparser import CParser, c_generator

p = CParser()
g = c_generator.CGenerator()
for src in ["_Alignas(4) _Alignas(16) int x;",
            "const _Atomic(int) x;",
            "const _Atomic(int *) p;",
            "_Atomic(int) a, b;",
            "int n = sizeof(const _Atomic(int *));"]:
    print(repr(g.visit(p.parse(src))))
```

## 期待結果

- 生成したコードは元の宣言と同じ意味になる（`_Alignas` と修飾子は失われず、各変数の名前が保たれる）
- 生成したコードを再び解析して生成しても同じ結果になる
- `_Alignas` や `_Atomic(型)` を含まない宣言の生成結果は変わらない

## 実際の結果

```text
'_Alignas(4) int x;\n'
'_Atomic int x;\n'
'int * _Atomic p;\n'
'_Atomic int a;\n_Atomic int a;\n'
'int n = sizeof(const int *);\n'
```

2 つ目の `_Alignas`、外側の `const` が消え、`b` が `a` として出力される。
