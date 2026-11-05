# 不具合報告: RRset を Rdataset と同じ引数で照合できない

作業ディレクトリの repository（dnspython）にある次の不具合を修正してください。

## 症状

`dns.rrset.RRset` は `dns.rdataset.Rdataset` の一種として扱えるはずだが、`Rdataset` と同じ引数（rdclass, rdtype, covers）で `match` を呼ぶと `TypeError` になる。RRset を Rdataset として扱うコードに渡すと、照合の段階で失敗する。また、名前を含めた照合を明示的に行う手段がない。

## 再現手順

```python
import dns.rdataclass
import dns.rdatatype
import dns.rrset

r = dns.rrset.from_text_list('foo', 30, 'in', 'a', ['10.0.0.1', '10.0.0.2'])

print(r.match(r.name, dns.rdataclass.IN, dns.rdatatype.A, dns.rdatatype.NONE))
for label, call in [
        ('Rdataset と同じ引数で match', lambda: r.match(dns.rdataclass.IN, dns.rdatatype.A, dns.rdatatype.NONE)),
        ('full_match', lambda: r.full_match(r.name, dns.rdataclass.IN, dns.rdatatype.A, dns.rdatatype.NONE))]:
    try:
        print(label, call())
    except Exception as exc:
        print(label, type(exc).__name__)
```

## 期待結果

- `match(rdclass, rdtype, covers)` を `Rdataset` と同じ引数で呼べ、`Rdataset.match` と同じ判定結果を返す
- これまでどおり、最初の引数に名前を渡す `match(name, rdclass, rdtype, covers, deleting=None)` の呼び方も同じ結果を返す（後方互換）
- 名前・class・type・covers・deleting のすべてで照合する `full_match(name, rdclass, rdtype, covers, deleting=None)` を呼べ、一致すれば `True`、名前・type・deleting のいずれかが違えば `False` を返す

## 実際の結果

```text
True
Rdataset と同じ引数で match TypeError
full_match AttributeError
```

名前を渡す呼び方は動くが、`Rdataset` と同じ引数での呼び出しは `TypeError` になり、`full_match` は存在しない。
