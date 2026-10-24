## 症状

route の callback が `close()` を持つオブジェクト（ファイルや独自の iterable など）を返したとき、まれな経路でそのオブジェクトが閉じられません。

## 再現手順

```python
import bottle

class Body:
    def __init__(self):
        self.closed = False
    def __iter__(self):
        return iter([b"OK"])
    def close(self):
        self.closed = True

body = Body()
app = bottle.Bottle()
app.route("/close")(lambda: body)
# WSGI で /close を呼び出し、レスポンスを読み終えたあとに body.closed を確かめる
```

## 期待結果

- 返り値が `["OK"]`・`[b"OK"]`・`"OK"`・`b"OK"`・それらの list のどれでも、レスポンスの処理の後で `close()` が呼ばれる。`start_response` の中で例外が起きた場合も同じ
- テスト補助（`test/tools.py`）はレスポンスを閉じるときに、モジュールの関数 `bottle._try_close(obj)` を呼ぶ。この関数は、obj が `close()` を持つときだけ呼ぶ

## 実際の結果

一部の経路で `close()` が呼ばれません。
