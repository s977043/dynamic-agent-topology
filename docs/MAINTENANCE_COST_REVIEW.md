# 保守コスト削減の調査と実行計画

2026-10-20チェックポイント。非規範的な提案であり、権限・必須CI・レビュー回数・Freezeを変更しない。優先するのは状態の再調査と重複作業の削減。未使用コード・不要依存・flaky testと確定した対象はなく、削除や隔離は提案しない。

## 根拠と限界

固定対象はmain [`3504a78`](https://github.com/s977043/dynamic-agent-topology/tree/3504a78)。10月16日の調査対象 `35b1c943c68f58880c857c5e52d61c6fbd8fa860` から、研究記録#203、release文書#186、Actions更新#210の3 commitが追加された。#210はCodeQL/Scorecard等のpin更新であり、旧pinを現行と扱わない。

- **静的調査:** workflow、requirements、schema、Python import、CLI文書、subprocess/importlib経路、実行計画とguidanceを参照。関数単位の完全call graph、全履歴、外部利用者は未調査。
- **動的経路:** probeの手動CLI、PDF処理、operator kitの動的import、retry監査のstatus分岐と既存記録を確認。コード上の到達可能性と実際の実行を区別する。新規モデルRun・workflow起動・権限変更は行わない。
- **実行履歴:** 10月16日のGET `/actions/runs?per_page=60` は60 SUCCESS（10月14〜16日）。選定runのGET `/actions/runs/{id}/jobs` によるvalidate 25〜30秒、mainのAnalyze Python 59秒・Scorecard 32秒は**旧標本**で、最新CI性能や課金ではない。並列job-wall秒の合計は待ち時間ではない。
- 10月20日の最新25 workflowには2 FAILUREを含む。旧60成功を最新結果として引用しない。同SHA・入力・runner差・再実行と失敗ログの因果を揃えていないため、失敗をflakyと分類しない。月間費用、中央値/p95、レビューの人時・追加tokenは未計測。

10月16日調査の選定run: [validate 38849402660](https://github.com/s977043/dynamic-agent-topology/actions/runs/38849402660)、[CodeQL 38849402655](https://github.com/s977043/dynamic-agent-topology/actions/runs/38849402655)、[Scorecard 38849402734](https://github.com/s977043/dynamic-agent-topology/actions/runs/38849402734)、validate `38849255684` / `38849164321` / `38849124006`。過去Observe `38481873935` FAILURE、Promote `38481873976` attempt 2 SUCCESSも、自動Draft経路の受理やflakeの証明にはしない。

## 候補

### C1 / P1 — 古いFreeze状態をguidanceから整理

- **Candidate:** `AGENTS.md` のactive前提の説明を、completed後の保全と現行状態参照へ整理するHuman-owned Draft。
- **Evidence:** AGENTSは「under Feature Freeze」、[実行計画](CURRENT_EXECUTION_PLAN.md)と`pilot/freeze.yaml`はcompleted revision 3。18/18 Runの完了後も旧33 blob監査はCIに残る。
- **Unknown:** 誤停止回数、再確認時間、token削減量。
- **Impact:** 不要な状態再調査を減らす可能性。
- **Risk:** 中。保全制約まで弱めればEvidenceの改変につながる。
- **Owner:** Maintainer / Harness責任者。guidanceのmergeはHuman。
- **Verification:** active/completed/異常statusの説明、旧33 blob、Operator境界、過去Run再実行禁止を照合し、guidance validatorと独立レビュー。
- **Rollback:** guidance変更commitをrevert。Frozen artifactは触らない。
- **Recommendation:** 別Draft [#215](https://github.com/s977043/dynamic-agent-topology/pull/215)に具体案を用意済み。本PRではguidanceを編集せず、Human mergeへ引き継ぐ。

### C2 / P1 — 反復レビューの適用範囲を計測

- **Candidate:** 変更のない再確認の費用と追加検出を記録し、将来の適用条件を提案する。
- **Evidence:** 実行計画は各作業3ループを指定。`AGENT_HARNESS.md` L-010に机上レビュー15回以上でRunが進まなかった記録。
- **Unknown:** 現行3ループの費用、不具合検出の増分。
- **Impact:** 内容不変の重複作業を減らせる可能性。
- **Risk:** 中。独立レビューや修正後検証を省けば見逃しが増える。
- **Owner:** Maintainer / レビュー運用責任者。
- **Verification:** 各loopのhead、指摘、修正、追加検出、elapsedを記録。必須CIと別セッションの独立レビューを維持。
- **Rollback:** 元のチェックリストを適用。
- **Recommendation:** 今回のユーザー明示の3ループを実施する。この候補で上書きしない。回数変更は別途判断。

### C3 / P2 — 文書中心のCI経路を計測して設計

- **Candidate:** 必須checkを常に生成するdispatcherと差分分類のshadow案。
- **Evidence:** `spec-lint.yml` / `codeql.yml`はmain pushとPRで起動し、CodeQLは週次も実行。旧標本ではAnalyze Pythonがvalidateより長い。現行pinは#210で更新済み。
- **Unknown:** 最新性能、queue、月額、docsの間接影響、分類精度。PR headとmerge commitの検査は同一ではない。
- **Impact:** 安全に対象外と判定できる変更のjob実行を削減できる可能性。金額未算定。
- **Risk:** 高。workflow全体のpaths-ignoreはrequired check待ちやSAST空白を招き得る。
- **Owner:** CI maintainer / security reviewer。
- **Verification:** docs/Python/schema/workflow/依存/renameのshadow分類、未分類full実行、check生成、失敗伝播、merge SHAと週次full scanを評価。
- **Rollback:** 常時full実行へrevert。required checks設定を維持。
- **Recommendation:** まず長期GET集計と設計。今回CIは変更せず、テスト削除で最適化しない。

### C4 / P2 — Harness publish経路の運用判断

- **Candidate:** Observe/Promoteの自動publishと観測専用運用を比較。
- **Evidence:** 最新Observe [39214997427](https://github.com/s977043/dynamic-agent-topology/actions/runs/39214997427)とPromote [39217402283](https://github.com/s977043/dynamic-agent-topology/actions/runs/39217402283)はmain `3504a78` で `API_HTTP_403`。生成ref/commitとAPI呼出し順はPR作成段階を示唆するが、ログ自体にendpointはなく、正確なpolicy原因は未確認。schedule / `--publish` / write権限が存在。[運用記録](HARNESS_LIVE_OPERATIONS.md)と[#159](https://github.com/s977043/dynamic-agent-topology/issues/159)は正規自動Draft受理と手動診断を区別する。
- **Unknown:** 現在の管理者設定、失敗原因、通知・復旧人時、次回成功可能性。
- **Impact:** 反復失敗の調査負担を減らせる可能性。
- **Risk:** 中。停止は有用な観測を失う。token迂回による権限拡大は対象外。
- **Owner:** Repository管理者 / Harness運用者。
- **Verification:** read-only設定照合、Draft/no-op/CIの受入条件と出力同等性。運用実行は既存の条件を満たしてから。
- **Rollback:** 保存したschedule/publish設定を復元し、生成branchとEvidenceを保持。
- **Recommendation:** #159の既存計画を使い、重複作業を起票しない。不要機能とは断定しない。

### C5 / P3 — 互換aliasの将来廃止

- **Candidate:** `requiredApprovingReviewCount`の移行可能性を調査。
- **Evidence:** settings schemaでdeprecated、`audit_repository_settings.py`で正規化、testsでlegacyと重複禁止を検証。自repo targetはExactを使用。
- **Unknown:** 外部target、保存データ、移行期間、削減量。
- **Impact:** 小。将来のschema分岐と互換testの簡素化。
- **Risk:** 中〜高。外部監査の互換性を壊す。
- **Owner:** Schema / compatibility maintainer。
- **Verification:** 利用調査、移行文書、正規/legacy/重複/不正値の互換テスト。
- **Rollback:** alias、正規化、testsを復元。旧入力を保存。
- **Recommendation:** 利用証拠が揃うまで保持。

### C6 / 保持 — 低参照probe・retry経路

- **Candidate:** 入口台帳を作り、低参照を未使用と誤認しない。
- **Evidence:** `knowledge_integrity_probe.py`は[Cloud計画](CLOUD_VERIFICATION_PLAN.md)と[実測](KNOWLEDGE_INTEGRITY_CLOUD_RESULTS.md)に手動入口があり、PDF処理は動的経路を含む。operator kitはimportlib、retry監査はactive条件付きでもtestsとcompleted原本監査が残る。
- **Unknown:** 外部利用、監査再現頻度、保存義務。
- **Impact:** 誤削除の調査を減らせる可能性。削除効果は不明。
- **Risk:** 高。再現性・歴史的Evidence・Frozen契約を失う。
- **Owner:** Experiment / Evidence maintainer。
- **Verification:** CLI、CI、動的import、operator kit、履歴再現の入口を照合。
- **Rollback:** 原本と入口を復元。Freeze改訂は別のHuman手続き。
- **Recommendation:** 保持。入口の少なさを削除根拠にしない。

### C7 / 保持 — 依存削減・flaky test隔離

- **Candidate:** 削除可能性より先に実利用と失敗原因を確認。
- **Evidence:** CIの`check-jsonschema` CLI、Pythonの`jsonschema` / `yaml` importが存在。PDF依存はdefault CIに追加されていない。最新25 runの2失敗だけではflakeを示さない。
- **Unknown:** 長期test単位失敗率、同SHA再実行、runner/network原因、transitive利用。
- **Impact:** 現時点で削減効果の証拠なし。
- **Risk:** 高。CLI/import破損やGuard回帰の見逃し。
- **Owner:** Python / test maintainer。
- **Verification:** CLI/直接/動的/transitive別利用表と、同SHAの失敗→成功のログ・再現条件を収集。
- **Rollback:** requirementsの元pinと必須test接続を復元。履歴を保存。
- **Recommendation:** requirementsもtestsも維持。不要・不安定と確定していない。

## 実行順序と完了条件

1. **通常PRで進める:** 本報告・indexとObserveのoffline回帰testを変更し、文書リンク・Freeze保全・拒否後の安全停止を検証。ユーザー指定3ループの独立レビュー、修正後の再検証、当該headの必須CI、未解決必須指摘0と現行HOTL条件を満たして通常mergeへ進める。回帰testはPOST PRの403伝播、生成ref保全、同入力retryの読取りのみでの停止を検証する。本番コード・権限は変更せずlive403解消の証明ではない。報告mergeはC1〜C7の広範な実装承認ではない。
2. **既存計画と統合する:** [#209](https://github.com/s977043/dynamic-agent-topology/pull/209)は状態同期の保留中PR。`CURRENT_EXECUTION_PLAN.md`の重複改訂を本PRへ持ち込まない。#186はmerge済みだがRelease未公開。未公開日表記の修正はDraft [#213](https://github.com/s977043/dynamic-agent-topology/pull/213)へ集約する。実公開日・tag・ReleaseはHuman所有で、merge済みを公開済みと扱わない。
3. **低リスクの次作業:** C1のHuman-owned guidance Draftを準備し、C2のloop記録とC3のread-only CI計測・shadow設計を別成果物にする。計測には取得時刻、SHA、全標本と失敗、job時間とqueueの定義を残す。新しい数値を得るまで削減率を約束しない。
4. **条件付き作業:** C4は管理者が#159の条件を確認。C5は外部互換性の証拠待ち。C6/C7は保持し、実験再実行・削除・隔離へ進まない。

研究Draft [#202](https://github.com/s977043/dynamic-agent-topology/pull/202)のGPT-6保守調査との重複は、C2/C3の計測・評価設計で照合する。研究候補はDATの採用契約ではなく、source claimから費用削減や設計有効性を断定しない。採用はDAT側Evidenceとsource ledger・対象Artifactの更新を別途必要とする。

DATは仕様と実験ベースであり、production runtimeを提供しない。それでも下流adoption、merge不能、Evidence喪失、権限境界への影響を各候補のリスクとして扱う。guidance、CI、Frozen artifact、requirementsの変更は本報告に含めない。
