# DAT手動dispatch canary（2026-11-03）

## 対象と完了条件

公開可能な小さいPython修正をT0とWorker→Verifierで各1回試す。構成選択の理由、実際のhandoff、独立した固定oracleによる結果、計測できた時間と欠測を残す。DATの自動dispatch実装や有効性の採用判断は行わない。

参照main: `95a4c8dad9564c1235108c0bee77161c0c1225ef`。開始時worktreeはclean、専用branch `research/dat-runtime-canary-20261103`。#291・#292はmerged、#288はdraftのまま。#287の人間計時、#248のfolding、#220のモデル役割分担と重複させない。これらの承認・完了条件は本canaryで満たさない。

## 構成選択

[dat-select](../../skills/dat-select/SKILL.md)をローカルファイルとして読み、[R0](../../policies/routing/R0_dynamic.yaml)の先頭分岐 `complexity: low, ambiguity: low` によりT0を選択した。辞書の選択規則が明示された1関数修正で、外部副作用がない。P0は固定テスト実行には十分だが未知の修正を作る役割は担わない。T1は比較候補としてのみ実行し、標準構成へ昇格しない。独立した助言ReviewerとVerifierを同一視しない。

## 実行方式の境界

- Plugin manifest/skillsの静的検証: `python scripts/validate_plugin.py` 成功。今回のhostへのPlugin登録・自動ロードは未検証。
- Skill利用: DATリポジトリの手順を明示的に読み適用した。Plugin経由の呼出しとは主張しない。
- orchestration: hostの通常collaborationツールを親が手動で呼び、別セッションに依頼する方式。DATコードによる選択結果からの自動dispatchではない。
- native: Codex CLI 0.159.2のhelpにagentsコマンドがあることを確認。ただしCLI model起動・custom role設定・native agents登録を試していない。CLIはPATH alias作成にread-only警告を出した。CLI版はhostのmodel/runtime版の証拠ではない。
- DATのREADME、Skill、Codex adapter、plugin manifestは自動applyしない契約で一致する。自動dispatchに進むには別のruntime mapping設計が必要。既存Skillに暗黙の起動機能を追加する変更は今回しない。

## 事前固定

[PLAN.md](PLAN.md)、[task.md](task.md)、[initial.py](initial.py)をworkers開始前にcommit。oracleは別セッションで作り、両workerへ結果を見せる前にhash固定する。原本planは英語のまま保存する。全fixtureは本検証のために作成した公開可能な合成データ。非公開プロジェクト資料・会話・認証・raw traceは含めない。

結果は後段に記録する。RunObservationやcanonical RunEvaluationではなく、このcanary固有の資料である。
