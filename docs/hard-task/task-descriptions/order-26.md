# 不具合報告: 後から componentType を与えた Sequence・Choice のクラスで、複製したインスタンスがスキーマを持たない

作業ディレクトリの repository（pyasn1）にある次の不具合を修正してください。

## 症状

`univ.Sequence` や `univ.Choice` を継承したクラスを `componentType` なしで定義し、インスタンスを作った後でクラスに `componentType` を代入する（再帰的なスキーマを定義するときに使う書き方）。この後、既存のインスタンスを `clone()` して作った新しいインスタンスも、クラスに代入したスキーマを持たず、代入したフィールド名に値を設定できない。

## 再現手順

```python
from pyasn1.type import univ, namedtype, tag


def show(label, func):
    try:
        print(label, "->", func())
    except Exception as e:
        print(label, "-> raised", type(e).__name__)


class LateSequence(univ.Sequence):
    pass

s = LateSequence()
LateSequence.componentType = namedtype.NamedTypes(
    namedtype.NamedType("name", univ.OctetString()))
show("Sequence: len(existing.componentType)", lambda: len(s.componentType))
show("Sequence: 'name' in existing", lambda: "name" in s)
c = s.clone()
show("Sequence: len(clone.componentType)", lambda: len(c.componentType))
def set_name():
    c["name"] = "abc"
    return c["name"]
show("Sequence: clone['name'] = 'abc'", set_name)


class LateChoice(univ.Choice):
    pass

ch = LateChoice()
LateChoice.componentType = namedtype.NamedTypes(
    namedtype.NamedType("number", univ.Integer()))
show("Choice: len(existing.componentType)", lambda: len(ch.componentType))
cc = ch.clone()
show("Choice: len(clone.componentType)", lambda: len(cc.componentType))
def set_number():
    cc["number"] = 123
    return cc.getName()
show("Choice: clone['number'] = 123", set_number)


class ParentSequence(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType("name", univ.OctetString()))

e = ParentSequence(componentType=namedtype.NamedTypes())
show("explicit empty: len(obj.componentType)", lambda: len(e.componentType))
show("explicit empty: len(clone().componentType)", lambda: len(e.clone().componentType))
show("explicit empty: len(subtype().componentType)", lambda: len(e.subtype(
    implicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatConstructed, 5)).componentType))
```

## 期待結果

- 代入より前に作った既存のインスタンスは、代入前のスキーマ（空）のまま一貫して扱われる（`len(componentType)` は 0、`'name' in s` は `False`）。これは今と同じ
- 既存のインスタンスを `clone()` して作った新しいインスタンスは、クラスに代入したスキーマを持つ。`Sequence` では `len(componentType)` が 1 になり、`clone['name'] = 'abc'` の後に `clone['name']` が `b'abc'` になる。`Choice` では `len(componentType)` が 1 になり、`clone['number'] = 123` の後に `getName()` が `'number'` になる
- コンストラクタに空の `componentType` を明示的に渡したインスタンスは、`clone()`（何回繰り返しても）・`subtype()` の後も空のスキーマを保つ。これは今と同じで、変えてはいけない

## 実際の結果

標準出力:

```text
Sequence: len(existing.componentType) -> 0
Sequence: 'name' in existing -> False
Sequence: len(clone.componentType) -> 0
Sequence: clone['name'] = 'abc' -> raised KeyError
Choice: len(existing.componentType) -> 0
Choice: len(clone.componentType) -> 0
Choice: clone['number'] = 123 -> raised KeyError
explicit empty: len(obj.componentType) -> 0
explicit empty: len(clone().componentType) -> 0
explicit empty: len(subtype().componentType) -> 0
```

`clone()` で作ったインスタンスもスキーマが空のままで、フィールドへの代入が `KeyError` になる。
