# 不具合報告: TSIG 付きのメッセージを wire 形式から読み込んで再び wire 形式にすると、元の TSIG レコードが保たれない

作業ディレクトリの repository（dnspython）にある次の不具合を修正してください。

## 症状

TSIG で署名した DNS メッセージを `dns.message.from_wire()` で読み込み、そのまま `to_wire()` で wire 形式に戻すと、読み込んだ TSIG レコードがそのまま出力されない。署名を検証せずに読み込んだ場合（`keyring=False`）は `to_wire()` が例外になり、検証して読み込んだ場合は元と異なる wire 形式になる。

## 再現手順

```python
import time
import dns.message
import dns.name
import dns.tsig

keyname = dns.name.from_text("keyname")
keyring = dns.tsig.Key(keyname, "NjHwPsMKjdN++dOfE5iAiQ==")

q1 = dns.message.make_query("example", "a")
q1.use_tsig(keyring, keyname)
wire = q1.to_wire()
time.sleep(1.1)

for label, kr in [("not verified", False), ("verified", keyring)]:
    q = dns.message.from_wire(wire, keyring=kr)
    try:
        print(label, "same wire:", q.to_wire() == wire)
    except Exception:
        print(label, "raised an exception")

q4 = dns.message.from_wire(wire, keyring=keyring)
q4.use_tsig(dns.tsig.Key(keyname, "abcd"))
print("after use_tsig with another key, same wire:", q4.to_wire() == wire)
```

## 期待結果

- 署名を検証せずに読み込んだ場合も、検証して読み込んだ場合も、`to_wire()` は例外なく元と同じ wire 形式を返す（`same wire: True`）
- 読み込んだ後に `use_tsig()` で別の鍵を指定した場合は、新しい TSIG で署名され、元と異なる wire 形式になる（`False`）

## 実際の結果

標準出力:

```text
not verified raised an exception
verified same wire: False
after use_tsig with another key, same wire: False
```
