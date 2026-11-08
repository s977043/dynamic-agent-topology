# 不具合報告: リンクをたどらない設定でも、循環するシンボリックリンクがあるとディレクトリの列挙が失敗する

作業ディレクトリの repository（python-pathspec）にある次の不具合を修正してください。

## 症状

`pathspec.util.iter_tree_entries()` に `follow_links=False` を指定して、互いを指す（または自分自身を指す）シンボリックリンクを含むディレクトリを列挙すると、リンクが列挙結果から欠け、リンクごとにエラーが `on_error` に渡される。同じディレクトリを `pathspec.util.iter_tree_files()` で列挙した場合は問題が起きない。

## 再現手順

```python
import os
import tempfile
from pathspec.util import iter_tree_entries, iter_tree_files

for case, links in [('Self', [('Loop', 'Loop')]),
                    ('Pair', [('First', 'Second'), ('Second', 'First')])]:
    with tempfile.TemporaryDirectory() as tmp:
        root = os.path.join(tmp, case)
        os.makedirs(os.path.join(root, 'Dir'))
        open(os.path.join(root, 'kept.txt'), 'w').close()
        open(os.path.join(root, 'Dir', 'child.txt'), 'w').close()
        for link, target in links:
            os.symlink(os.path.join(root, target), os.path.join(root, link))

        errors = []
        entries = sorted(e.path for e in iter_tree_entries(root, follow_links=False, on_error=errors.append))
        print(case, "entries:", entries, "errors:", len(errors))

        errors = []
        files = sorted(iter_tree_files(root, follow_links=False, on_error=errors.append))
        print(case, "files:", files, "errors:", len(errors))
```

## 期待結果

- `iter_tree_entries()` はエラーを報告せず（`errors: 0`）、`Dir`、`Dir/child.txt`、`kept.txt` と、各リンク（`Self` では `Loop`、`Pair` では `First` と `Second`）を返す
- `iter_tree_files()` の結果はこれまでどおり（エラーなし、ディレクトリ `Dir` を除く同じ項目）

## 実際の結果

標準出力:

```text
Self entries: ['Dir', 'Dir/child.txt', 'kept.txt'] errors: 1
Self files: ['Dir/child.txt', 'Loop', 'kept.txt'] errors: 0
Pair entries: ['Dir', 'Dir/child.txt', 'kept.txt'] errors: 2
Pair files: ['Dir/child.txt', 'First', 'Second', 'kept.txt'] errors: 0
```

`iter_tree_entries()` の結果にリンクが含まれず、リンクの数だけエラーが報告される。macOS で観測した。
