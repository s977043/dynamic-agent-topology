# 不具合報告: 独自の lexer と cache=True を併用すると 2 回目の構築で失敗する

作業ディレクトリの repository（lark）にある次の不具合を修正してください。

## 症状

`Lark(..., lexer=<独自の Lexer クラス>, cache=True)` で parser を作ると、1 回目は動くが、同じ文法・同じ設定で 2 回目に作ると（cache から読み込む経路で）例外が出て parser を作れない。

## 再現手順

カレントディレクトリに cache ファイル（`.lark_cache_*.tmp`）がない状態で実行する。

```python
from lark import Lark
from lark.lexer import Lexer, Token

class CustomLexer(Lexer):
    def __init__(self, lexer_conf):
        pass

    def lex(self, data):
        for obj in data:
            yield Token('A', obj)

g = 'start: A\nA: "a"\n'
print(Lark(g, parser='lalr', lexer=CustomLexer, cache=True).parse('a'))
print(Lark(g, parser='lalr', lexer=CustomLexer, cache=True).parse('a'))
```

## 期待結果

- 2 回とも parser を作れ、`parse('a')` が `Tree('start', [Token('A', 'a')])` を返す
- 同じ文法・同じ設定であれば、cache は 1 つだけ作られ、2 回目はそれを使う
- 独自の lexer を使わない場合の cache の動作は変わらない

## 実際の結果

```text
Tree(start, [Token(A, 'a')])
AttributeError: 'functools.partial' object has no attribute 'deserialize'
```

1 回目は期待どおりの木を返し、カレントディレクトリに cache ファイルが 1 つできる。2 回目の `Lark(...)` の構築で `AttributeError` が出る（出力は例外の最終行）。cache ファイルが残った状態で再び実行すると、1 回目の構築から同じ例外が出る。
