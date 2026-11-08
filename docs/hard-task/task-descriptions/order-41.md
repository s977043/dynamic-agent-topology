# 不具合報告: for 文の宣言リストから C を生成すると 2 つ目以降の宣言のポインタ・配列指定が消える

作業ディレクトリの repository（pycparser）にある次の不具合を修正してください。

## 症状

`for (char *s = 0, *t = 0; ;)` のように、for 文の初期化部に複数の変数をまとめて宣言したソースを解析し、`CGenerator` で C のソースに戻すと、2 つ目以降の宣言からポインタ（`*`）・配列（`[4]`）・関数ポインタ（`(*fp)(double)`）の指定が消える。生成されたソースは、元とは型の違う宣言になる。

## 再現手順

```python
from pycparser import CParser
from pycparser.c_generator import CGenerator

src = """
void g(void) {
    for (char *s = 0, *t = 0; ;) {}
    for (long n = 0, v[4] = {0}; ;) {}
    for (double x = 0, (*fp)(double) = 0; ;) {}
}
"""
print(CGenerator().visit(CParser().parse(src)))
```

## 期待結果

- 生成されたソースでは、2 つ目以降の宣言もそれぞれのポインタ・配列・関数の指定を保つ（例: `for (char *s = 0, *t = 0;;)`、`for (long n = 0, v[4] = {0};;)`、`for (double x = 0, (*fp)(double) = 0;;)`）
- 共通の型指定子と修飾子（`const`、`volatile`、`_Atomic(...)`、struct の定義、typedef 名など）は、これまでどおり最初の宣言にだけ書かれる
- 生成したソースを再び解析すると、元のソースと同じ構造になる

## 実際の結果

```text
void g(void)
{
  for (char *s = 0, t = 0;;)
  {
  }

  for (long n = 0, v = {0};;)
  {
  }

  for (double x = 0, fp = 0;;)
  {
  }

}

```

2 つ目以降の宣言が名前だけになり、`t` は `char`、`v` は `long`、`fp` は `double` の宣言として出力される。
