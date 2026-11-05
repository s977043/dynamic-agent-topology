# 不具合報告: 相対名と絶対名を含む rdata の比較が誤り、ゾーンの digest が表記で変わる

作業ディレクトリの repository（dnspython）にある次の不具合を修正してください。

## 症状

名前を含む rdata（例: CNAME、NS、MX）の比較で、次のことが起きる。

- 絶対名の `host.` と相対名の `host` の rdata が `==` で等しいと判定される
- 相対名を含む rdata どうし、または相対名と絶対名の rdata の間で、`<` などの大小比較が値を返す。相対名は origin が決まらないと順序が定まらないため、大小比較はできないはずである

この影響で、同じゾーンを `relativize=True` と `relativize=False` で読み込むと、`compute_digest` の結果（ZONEMD の digest）が異なることがある。

## 再現手順

```python
import textwrap

import dns.rdata
import dns.zone

a = dns.rdata.from_text('IN', 'CNAME', 'host.')
r = dns.rdata.from_text('IN', 'CNAME', 'host')
s = dns.rdata.from_text('IN', 'CNAME', 'other')
for label, x, y in [('absolute vs relative', a, r), ('relative vs relative', r, s)]:
    print(label, 'eq', x == y, 'ne', x != y)
    for op in ['<', '<=', '>', '>=']:
        try:
            print(' ', op, eval('x ' + op + ' y'))
        except Exception as exc:
            print(' ', op, type(exc).__name__)

text = textwrap.dedent('''
@  3600  IN  SOA  ns admin 1 7200 900 1209600 3600
   3600  IN  NS   ns
   3600  IN  MX   10 mail.example.org.
   3600  IN  MX   10 mail.
''')
digests = []
for relativize in [True, False]:
    z = dns.zone.from_text(text, 'example.org.', relativize=relativize)
    digests.append(z.compute_digest(dns.zone.DigestHashAlgorithm.SHA384).digest.hex()[:16])
print('digest relativize=True ', digests[0])
print('digest relativize=False', digests[1])
```

## 期待結果

- 絶対名と相対名の rdata は等しくない（`==` が `False`、`!=` が `True`）
- 相対名を含む rdata が関わる `<`、`<=`、`>`、`>=` は、`dns.rdata.NoRelativeRdataOrdering` 例外を送出する（相対名どうしでも、相対名と絶対名の間でも）
- 絶対名どうしの比較は、これまでどおり等値・大小の結果を返す
- 同じゾーンの `compute_digest` の結果は、`relativize=True` と `relativize=False` のどちらで読み込んでも同じになる

## 実際の結果

```text
absolute vs relative eq True ne False
  < False
  <= True
  > False
  >= True
relative vs relative eq False ne True
  < True
  <= True
  > False
  >= False
digest relativize=True  933d802dde68abae
digest relativize=False 1dbfebe68638aba7
```

`host.` と `host` が等しいと判定され、相対名を含む大小比較が値を返す。digest は `relativize` の指定で異なる。
