# 不具合報告: open type を持つ SEQUENCE を CER・DER で符号化した結果が期待するバイト列にならない

作業ディレクトリの repository（pyasn1）にある次の不具合を修正してください。

## 症状

`opentype.OpenType` で型が決まる `Any` の要素（タグなし、implicit タグ付き、explicit タグ付き）を持つ `Sequence` を、`asn1Spec` を指定して CER または DER の encoder で符号化すると、期待するバイト列にならない。

## 再現手順

```python
from pyasn1.type import namedtype, opentype, tag, univ
from pyasn1.codec.cer import encoder as cer_encoder
from pyasn1.codec.der import encoder as der_encoder

open_type = opentype.OpenType('id', {1: univ.Integer(), 2: univ.OctetString()})
blob_types = {
    "untagged": univ.Any(),
    "implicit": univ.Any().subtype(implicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 3)),
    "explicit": univ.Any().subtype(explicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 3)),
}
for kind, blob in blob_types.items():
    s = univ.Sequence(componentType=namedtype.NamedTypes(
        namedtype.NamedType('id', univ.Integer()),
        namedtype.NamedType('blob', blob, openType=open_type)))
    s[0] = 1
    s[1] = univ.Integer(12)
    for name, enc in [("CER", cer_encoder), ("DER", der_encoder)]:
        print(kind, name, tuple(enc.encode(s, asn1Spec=s)))
```

## 期待結果

次のバイト列になる。

```text
untagged CER (48, 128, 2, 1, 1, 49, 50, 0, 0)
untagged DER (48, 5, 2, 1, 1, 49, 50)
implicit CER (48, 128, 2, 1, 1, 163, 128, 163, 128, 49, 50, 0, 0, 0, 0, 0, 0)
implicit DER (48, 9, 2, 1, 1, 131, 4, 131, 2, 49, 50)
explicit CER (48, 128, 2, 1, 1, 163, 128, 163, 128, 49, 50, 0, 0, 0, 0, 0, 0)
explicit DER (48, 9, 2, 1, 1, 163, 4, 163, 2, 49, 50)
```

`SetOf` の要素として open type を持つ場合も、同じ考え方で符号化される。

## 実際の結果

標準出力:

```text
untagged CER (48, 128, 2, 1, 1, 2, 1, 12, 0, 0)
untagged DER (48, 6, 2, 1, 1, 2, 1, 12)
implicit CER (48, 128, 2, 1, 1, 163, 128, 2, 1, 12, 0, 0, 0, 0)
implicit DER (48, 8, 2, 1, 1, 131, 3, 2, 1, 12)
explicit CER (48, 128, 2, 1, 1, 163, 128, 2, 1, 12, 0, 0, 0, 0)
explicit DER (48, 8, 2, 1, 1, 163, 3, 2, 1, 12)
```
