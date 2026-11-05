# Workerへの共通依頼

両workerには次の同一テンプレートを渡した。`<arm>`のみ `t0` / `t1` に置換し、`<scratch>`はその実行用scratch rootに置換した。fork_turns=none、model/effort overrideなし。hostから共通で与えられるsystem/developer instructionsの完全一致は検査できていない。

```text
Bounded Python repair task. Read <scratch>/input/task.md and repair <scratch>/<arm>/solution.py. Standard library only. Read and write only these supplied task/solution files; do not inspect sibling directories, repo, oracle or other runs. Do not delegate, access network, change permissions or launch model APIs/CLI. You may run your own in-memory checks. Complete within 10 minutes. Final answer briefly report changed behavior, checks and unresolved issues. This is a public synthetic fixture.
```

これは新規作成の公開fixture用依頼。実ユーザーの会話やprivate資料を転記したものではない。
