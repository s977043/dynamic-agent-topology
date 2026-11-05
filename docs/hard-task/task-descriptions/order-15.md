# 不具合報告: `for_json()`・`_asdict()` を持つオブジェクトの符号化で、呼び出し回数とエラー時の注記が正しくない

作業ディレクトリの repository（simplejson）にある次の不具合を修正してください。

## 症状

`simplejson.dumps()` の Python 実装で、次の 2 つの問題が起きる。

1. `for_json=True` を指定し、`for_json()` と `_asdict()` がどちらも `TypeError` を送出するオブジェクトを符号化すると、それらのメソッドが 1 回ずつではなく複数回呼ばれることがある（値をリストや dict に入れた場合）
2. 符号化できない値で `TypeError` になったとき、例外に付く注記（`__notes__`、Python 3.11 以降）が、どの容器のどの要素を処理していたかを正しく示さない。`_asdict()` を持つ値の後にある要素で失敗した場合や、`_asdict()` が dict 以外を返した場合に起きる

## 再現手順

```python
import collections
import simplejson as json

calls = []

class Raises(object):
    def for_json(self):
        calls.append('for_json')
        raise TypeError('nope')
    def _asdict(self):
        calls.append('_asdict')
        raise TypeError('nope')

for value in (Raises(), [Raises()], {'k': Raises()}):
    del calls[:]
    print(json.dumps(value, for_json=True, default=lambda o: 'd'), calls)

class D(dict):
    pass

NT = collections.namedtuple('NT', 'x')
try:
    json.dumps(D([('a', NT(1)), ('b', object())]))
except TypeError as exc:
    print("notes:", getattr(exc, '__notes__', None))

class NotADict(object):
    def _asdict(self):
        return [1]

try:
    print(json.dumps({'a': NotADict()}))
except TypeError as exc:
    print("error:", exc, "notes:", getattr(exc, '__notes__', None))
```

## 期待結果

- 3 つの値はそれぞれ `"d"`、`["d"]`、`{"k": "d"}` に符号化され、どの場合も呼び出しは `['for_json', '_asdict']`（各 1 回）になる
- `D` の例では、注記が、符号化に失敗した値と、それを含む実際の容器 `D` のキー `b` を正しく示す
- `NotADict` の例では、不正な戻り値による失敗として報告され、注記が実際の外側の dict のキー `a` を正しく示す

## 実際の結果

標準出力:

```text
"d" ['for_json', '_asdict']
["d"] ['for_json', '_asdict', 'for_json', '_asdict']
{"k": "d"} ['for_json', '_asdict', 'for_json', '_asdict']
notes: ['when serializing object object', "when serializing dict item 'b'"]
error: _asdict() must return a dict, not list notes: ["when serializing list item 'a'"]
```

C 拡張は build していない状態（Python 実装）で観測した。リストと dict に入れた場合は各メソッドが 2 回呼ばれ、注記の容器の名前が実際の容器（`D`、`dict`）と異なる。
