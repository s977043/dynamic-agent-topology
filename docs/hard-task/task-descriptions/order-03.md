# 不具合報告: _Static_assert の後のセミコロンの扱いが C の文法と合わない

作業ディレクトリの repository（pycparser）にある次の不具合を修正してください。

## 症状

`_Static_assert` の宣言について、次の 2 つが起きる。

- 関数本体の中で `_Static_assert(...);` と書くと、宣言の後ろに余分な空文（`EmptyStatement`）が 1 つずつ追加される
- 末尾のセミコロンがない `_Static_assert(...)` が、エラーにならずに受理される

## 再現手順

```python
from pycparser import CParser

p = CParser()
ast = p.parse('void f(void) { _Static_assert(3, "block"); _Static_assert(4);; int x; }')
print([type(n).__name__ for n in ast.ext[0].body.block_items])

for src in ['_Static_assert(1, "ok")',
            '_Static_assert(1) int x;',
            'void f(void) { _Static_assert(1) }']:
    print([type(n).__name__ for n in p.parse(src).ext])
```

## 期待結果

- 1 つ目の出力は `['StaticAssert', 'StaticAssert', 'EmptyStatement', 'Decl']`（書かれた `;;` の 2 つ目だけが空文になる）
- セミコロンのない 3 つの入力は、いずれも `ParseError` になる
- ファイルの先頭でも関数本体の中でも、`_Static_assert(...);` はそれ自体が 1 つの宣言として扱われる

## 実際の結果

```text
['StaticAssert', 'EmptyStatement', 'StaticAssert', 'EmptyStatement', 'EmptyStatement', 'Decl']
['StaticAssert']
['StaticAssert', 'Decl']
['FuncDef']
```

関数本体の中では各 `_Static_assert` の後に空文が 1 つずつ余分に入り、セミコロンのない入力は 3 つとも受理される。
