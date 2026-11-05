# 不具合報告: 一部の rdata type 名が RdataType.make では受け付けられない

作業ディレクトリの repository（dnspython）にある次の不具合を修正してください。

## 症状

rdata type の名前を値に変換する方法として、`dns.rdatatype.from_text()` と `dns.rdatatype.RdataType.make()` がある。多くの名前では両者は同じ結果を返すが、次の名前では `from_text()` が成功するのに `RdataType.make()` が `UnknownRdatatype` で失敗する。

- `NSAP-PTR`（名前にハイフンを含む type）
- `dns.rdata.register_type()` で利用者が登録した type の名前（大文字・小文字どちらでも）

## 再現手順

```python
import types
import dns.rdata
import dns.rdatatype
import dns.rdtypes.txtbase

mod = types.ModuleType("ttxt")
class TTXT(dns.rdtypes.txtbase.TXTBase):
    pass
mod.TTXT = TTXT
dns.rdata.register_type(mod, 64001, "TTXT")

for text in ["NSAP-PTR", "TTXT", "ttxt"]:
    for name, func in [("from_text", dns.rdatatype.from_text),
                       ("RdataType.make", dns.rdatatype.RdataType.make)]:
        try:
            print(name, repr(text), "->", repr(func(text)))
        except Exception as e:
            print(name, repr(text), "-> raised", type(e).__name__)
```

## 期待結果

- `RdataType.make()` は、上の 3 つの名前すべてで `from_text()` と同じ値を返す（`NSAP-PTR` は `dns.rdatatype.NSAP_PTR`、`TTXT` と `ttxt` は登録した 64001）
- `from_text()` の結果は今と変わらない

## 実際の結果

標準出力:

```text
from_text 'NSAP-PTR' -> <RdataType.NSAP_PTR: 23>
RdataType.make 'NSAP-PTR' -> raised UnknownRdatatype
from_text 'TTXT' -> 64001
RdataType.make 'TTXT' -> raised UnknownRdatatype
from_text 'ttxt' -> 64001
RdataType.make 'ttxt' -> raised UnknownRdatatype
```

`from_text()` は 3 つとも成功し、`RdataType.make()` は 3 つとも `UnknownRdatatype` になる。
