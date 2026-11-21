# Subagent folding: 最小検証計画と合成oracle（#248）

状態（2026-11-15再確認）: **合成oracle検証済み / 実モデル NOT_TESTED / Runtime実行可能性HOLD**。
本書は実験開始、予算消費、採用、既定設定変更の許可ではない。
初期実装時の基準main: `7eae35b2f29bb0903aab21f3637d587c48c2c7ea`（2026-11-03取得）。
現行確認main: `c350786bd9e9341e1eed744ab440f6b402d5b0c4`（2026-11-15取得）。
合成oracleを含む [PR #288](https://github.com/s977043/dynamic-agent-topology/pull/288) は
2026-11-08にマージ済み（レビュー経緯はPRを参照）。実モデルのfold/keep判定は未実施。
追跡: [Issue #248](https://github.com/s977043/dynamic-agent-topology/issues/248)。

## 1. 今回答える問い

専門Subagent 1つをMain Loop内のSkillへ移した場合に、必須の業務確認を
省略せず、同じ要求を達成できるか。まず「判定器が省略を検出できること」を
費用のかからない合成fixtureで確認する。速度・品質の効果はまだ測定しない。

最初のtask classは、**許可された注文の配送予定日数を確認して回答するread-only処理**。
必須の系列は `lookup_order → lookup_eta → respond`。
注文IDと正しい日数は評価者が固定する。回答が正しくても配送確認を省略したら不合格。
これはDAT側で独自に作成した合成ケースで、実顧客・実配送データではない。

全システムの全経路を網羅するまで準備を続けない。まずこの宣言済みの系列だけを
対象にする。未登録の拒否・配送情報なし・複数注文などへ結論を広げない。

## 2. 既存研究と変更境界

| 対象 | 今回との関係 |
| --- | --- |
| EXP-001 / #15 | 既存結果・Frozen inputsは変更しない。T0/T1結果をfoldingの効果へ転用しない |
| #93 / #88 | selector / cascade / escalationを追加しない |
| #220 | model splitとは別。F0/F1でModel・Effortを同時変更しない |
| #268 / vNext | [RFC](rfc/DAT_VNEXT_RFC.md)の再設計比較とは別の試験。新Runtime/Skill/公開CLIを作らない |
| #248 | 本書の対象。F0/F1の限定的な比較準備だけを進める |

正本は [実験規約](EXPERIMENTS.md)、[指標](METRICS.md)、
[Agent運用規約](AGENT_HARNESS.md)。本書から権限・評価規約を上書きしない。
外部OSS・SDK・Skillの取込みや依存追加はない。

出典の入口はIssue #248。Anthropic kitのREADMEを今回再取得し、reference実装であること、
offline stand-inの動作確認を実モデルのスコアと区別する記述を確認した
（`anthropics/single-agent-loop-kit`, `README.md` blob
`bca6950cd54d176e3220be6f15c30f427589dc91`）。外部コードは複製していない。
元記事ページは今回再取得できなかったため、「約2倍」などの数値は本書の効果予測や
今回確認した事実として採用しない。研究候補の採用状態は変更しない。

## 3. 今回実装する範囲

- [oracle](../scripts/subagent_folding_oracle.py): 標準ライブラリのみのpure function。
  CLI・ファイル保存・ネットワーク・モデル呼出し・外部操作はない。
- [合成テスト](../scripts/test_subagent_folding_oracle.py): 正常、手順の欠落・順序逆転、
  別注文、別Run、失敗したtool、欠測、不正型、リトライ、actor名変更を検査。
- 既存`spec-lint`へテストを1ステップ追加。既存チェック・依存・権限は変更しない。

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/test_subagent_folding_oracle.py
```

### 判定の意味と限界

| 結果 | 意味 |
| --- | --- |
| PASS | 入力された合成観測が、系列・対象・値・最終回答のACを満たす |
| FAIL | 完全な観測として渡されたfixtureに、手順欠落・誤対象・誤値・回答欠落などがある |
| INCONCLUSIVE | 完全性不明、Run混在、未対応イベント、不正型、必要な結果データ欠測 |
| ValueError | 評価者が与える正解Case自体が不正。モデルの失敗として集計しない |

`Event`はこのfixture内の型であり、新しいcanonical Artifact/Schemaではない。
生のRuntime traceを読み込む機能はない。実測へ使う前に、別途レビューした変換が必要。
`run_id`の一致や`trace_complete=True`だけでは、ログの真正性・完全性を証明しない。
自己申告や生成された要約を入力して実行証跡と扱わない。独立取得したtool結果、最終応答、
欠測判定との照合が必要で、現時点ではそのRuntime接続は **NOT_TESTED**。

判定はactor名を使わない。同じ正しい系列ならmainでもspecialistでも同じ結果になる。
これはTopology中立なoracleのテストであり、実際のF0/F1実行や独立Contextの証明ではない。
失敗toolは必要手順に数えないが、回答前の正当な再試行は許す。別注文への操作試行は、
拒否された場合もこのfixtureではFAIL。これをRuntimeによるアクセス制御の実証としない。

合成テスト数は実験のtask数・Run数・paired block数ではない。
本oracleのPASSは、E2E実モデル品質、非劣性、性能、コスト削減、安全制御の実効性を意味しない。

## 4. F0/F1の比較設計（未実行）

| arm | 構成 | 保持するもの |
| --- | --- | --- |
| F0 | Main + 配送確認の専門Subagent 1つ | domain手順、工具の契約、同じ評価器・安全制御 |
| F1 | Main + 同等のdomain手順を持つ必要時ロードSkill | F0と同じ要求・正解・toolデータ・実効権限 |

F0/F1はこの試験の識別名で、canonical T0/T1等を改定しない。
Context境界、handoff、Skillロードがまとめて変わる**複合介入**。
結果が出ても、各要因単独の効果や「Skills一般の効果」とは主張しない。
F2（常時ロード）とF3（選択的Subagent）は最初の比較から外す。

固定・記録するもの: Task/AC/oracleのSHA、domain手順の内容、fixture、Runtime/CLI/tool版、
実効Model ID・Effort、利用可能なTools、実効権限、予算、停止条件、再試行規則。
F0の限定権限をF1で単にunionして広げない。同等に強制できなければfoldを保留する。
独立Reviewer/VerifierとHumanの承認境界は統合対象外で、両armで同条件に保持する。
F0のSubagent起動とF1のSkillロードは実トレースでactivationを確認する。

### 最小の実モデルfeasibility案

事前登録・Operator条件を満たした後の**提案**であり、実行許可ではない。
配送日数0/3/7の3ケース × 2反復 × F0/F1 = 12 Run、6 paired blocksを上限候補とする。
各ケースで先行armを反転し、毎Run fresh workspace / fresh session。
arm間で出力・学び・会話を引き継がない。キャッシュ方針を固定・記録し、
provider側で制御不能なキャッシュや実行環境の差は交絡として残す。

ここで確認するのは両armの実行・計測・回帰検出が成立するかだけ。
小標本から品質非劣性・p95改善・本番採用を結論しない。
全Run合格でも次段階の判定はfeasibility完了に限り、fold採用は別判断。
失敗・timeout・abort・未発火・片側欠測を消して成功例だけを比較しない。

| 観測 | 記録方法 |
| --- | --- |
| verified outcome / 必須手順 | 固定oracle + 独立取得したtool結果・最終応答。自己申告を正解としない |
| regression | paired blockでF0成功→F1失敗を別掲。平均成功率で隠さない |
| activation | specialist呼出し/Skillロードの実ログ。宣言だけなら不明 |
| wall time | 同じ開始/終了境界の単調時計。並行legの時間を合計してwall timeにしない |
| tokens / model calls | Main、Subagent、リトライ、失敗/破棄legをすべて含む |
| 費用 | 実usageと適用価格を確認できる場合のみ算定。契約内追加支出と換算原価を分離 |
| 評価・人間の負担 | 共通評価処理の費用を別掲し総費用にも含める。介入回数から認知負荷を推定しない |

既存`ExecutionTrace`/`RunEvaluation`と`blockId`を再利用する方針。
具体的なRuntime mapping・欠測・計測対応は実行前に確認し、未対応項目を0で埋めない。

### 実行前に残る項目

1. 実効Model/Runtime/Skillロード・subagent起動・trace取得と、同等権限の確認。
2. train/regressionの合成fixtureと採否判定testの分離。今回公開テストはoracle開発用であり、
   後続のheld-out品質評価へ流用しない。fixture/手順/AC/oracleの版を固定する。
3. Run数、wall-time/token上限、全legへの強制方法、再試行、失敗・欠測・停止規則、
   Operatorの契約/追加課金境界を事前登録しレビュー。上限や追加課金が不明なら起動しない。
4. 独立Reviewerが固定版を確認。Operatorが承認済み条件で実行する。
5. 重大な権限違反、失敗を成功とする誤判定、Runtime/Model変更、予算境界不明で停止。
   完全性不明・arm未発火・paired条件不成立はINCONCLUSIVE。条件を変える再開は別版にする。

後続の効果評価では、対象母集団、実用上の品質非劣化幅、コスト/遅延の改善幅、
必要block数、不確実性の扱いを結果を見る前に固定する。本書はその効果評価の事前登録ではない。

## 5. 初期実装時の5ループと引継ぎ（履歴）

すべて作成セッションの**自己レビュー**。別セッション独立レビューの代替ではない。

| loop | 検証・発見・修正 | 修正後の局所結果 |
| --- | --- | --- |
| 1 | 回答だけでなく注文・配送確認の存在を検査 | 4 tests PASS |
| 2 | 順序逆転、回答後の確認、別注文が初版を通る3件を負側テストで再現。順序/対象を検査 | 7 tests PASS |
| 3 | 未知イベントを黙って無視する誤受理を再現。欠測/Run混在/失敗toolも区別 | 15 tests PASS |
| 4 | 文字列successとbool数値の誤受理、正解Caseの不正を検出。型・正解値を検査し、再試行/actor中立性を確認 | 27 tests PASS |
| 5 | 不正イベント/応答重複/必須metadataを追加検査。既存CIへ1ステップだけ追加し差分を確認 | 34 tests PASS（ローカルPython 3.13.5） |

Python 3.12・全リポジトリの結果はPR CIで別途確認する。
ローカルには完全なcloneがなく、対象ファイルの局所テストだけを行った。
CIの対象headと結果、5ループの詳細、独立レビュー結果はPRへ記録する。

### 別セッションReviewerへの依頼

Issue #248、PRの最新headと4ファイルの全差分を一次材料として読む。
本書の要約だけでレビューしない。以下を確認してruntime/model/session ID、対象head、
必須/推奨指摘、根拠、判定をPRに残す。

- 実モデルの有効性や独立レビューを実施済みと誤表示していないか。
- 同じtaskをF0/F1に中立に評価できるか。手順省略・順序・不正値・欠測の誤受理がないか。
- 既存CI/EXP-001/Schema/Skills/権限を弱めず、追加依存や課金経路がないか。
- 上記コマンドとPython 3.12 CIを再確認し、実測準備の未達を維持しているか。

初期PR #288はspec-lintへの検証step追加を含むため、同種の#279と当時のAGENTS/Harnessに従い規則変更PRとして扱い、Humanがmergeする条件だった。既存検査は弱めない。別モデルの独立レビュー、未解決必須指摘0、最新headの必須CI成功を確認し、Issue #159へリンクを記録する。モデル相違の証跡がなければ別モデルレビュー条件を満たしたと扱わない。
初期PR #288がmergeしてもIssue #248は閉じない。残タスクはRuntime接続・事前登録・Operator実測・
限定的な結果評価であり、本準備PRの完了とは分離する。

## 6. P0 Runtime実行可能性チェック（2026-11-15）

最初のVertical Sliceは新しいAgent・Skill・Runnerの作成ではなく、
**F0/F1を同一Runtimeで起動・観測するための手段と、権限制約を事前に特定できるか**
のread-only確認とする。実際の起動・発火・権限強制の検証はOperator/HOTL承認後に分離する。
設計書の合成ケースは選定済みで、34件のoracleテストはPython 3.12.14でPASS。
`validate_semantics.py`と`validate_experiments.py`も同じmainでPASSした。
これらは実Runtimeの検証ではない。

| 確認項目 | 2026-11-15の根拠 | 現在の判定 |
| --- | --- | --- |
| DATのF0/F1設計・合成oracle | §3〜4、PR #288のmerged内容 | 準備済み（実モデル未実行） |
| DATからRuntime設定の自動適用 | `adapters/{codex,claude-code}/README.md`はManual Adapter | 未実装（手動対応が必要） |
| Runtime Capabilityの宣言と実効検査 | [Codex Adapter](../adapters/codex/README.md) / [Claude Code Adapter](../adapters/claude-code/README.md) に実行方式別の根拠を分離 | 実効境界・発火はNOT_TESTED |
| F0専門Subagentの起動とF1 Skillロード | Runtime由来のactivation traceなし | NOT_TESTED |
| F0/F1の実効Model/Effort・Tool・Permission同等性 | 実行時の独立観測なし | NOT_TESTED |
| 生traceの真正性・欠測とoracleへの変換 | §3のoracleは合成`Event`のみを受理 | NOT_TESTED |
| Operator・予算・通信先・証拠保存先 | #248の実行条件が未承認 | HOLD |

### P0の着手順と判定

1. 候補Runtime・CLI version・対象commitを記録し、read-onlyの専門処理を1つ選ぶ。
   独立Reviewer/Verifierや承認主体はfold候補から除外する。
2. F0のSubagent起動方法とF1のSkill読込み方法、各々の正本・配布経路を棚卸しする。
   **定義・インストール済み**と**実際に発火した**ことの証拠要件を分け、
   後者は実行まではNOT_TESTEDと記録する。
3. 両armのTool/Permission設定と強制方法の候補を対応表にし、F1に権限を単純にunionしない。
   Capability宣言を実効権限の証明と読み替えない。Runtime別の確認はAdapterの正本に従う。
4. 生のTool結果・最終応答・activation・欠測を独立取得する予定の手段を特定し、
   `ExecutionTrace`/`RunEvaluation`/`blockId`への対応と変換損失の候補を記録する。
   自己申告・合成fixture・メタデータ比較器の結果だけで真正性を認定しない。
5. 起動手順・観測手段・権限制約の静的な前提が特定できなければ**HOLD**。
   特定できた場合に限り、held-outケース、全leg予算、再試行・中断規則と
   DATのAgent Harness規約に基づくOperator/HOTL実行承認を別途取得する。
   承認後の限定feasibilityで
   初めて実際のactivation・実効権限・Trace完全性を確認する。

現時点のGOはP0の読み取り調査とオフライン検査に限定する。
12 Run/6 paired blocksは承認後のfeasibility候補であり、品質非劣性・p95・採用効果は判定しない。
Secret/PIIの外部送信、権限拡大、欠測のPASS化、未承認の有料モデル起動はSTOPとする。

### P0 read-only調査の追加結果（2026-11-15）

初期候補Runtimeの静的調査は管理作業環境で実施した履歴であり、Operator実機の状態ではない。実モデルは起動していない。Runtime固有のCLI版・機能宣言・権限・Trace候補と読み取り専用コマンドは、[Codex Adapter](../adapters/codex/README.md)および[Claude Code Adapter](../adapters/claude-code/README.md)に分離して記録する。

DAT共通の未解決事項は、同一配送ETAタスクに対応するF0/F1実体、両armの実効権限の同等性、独立に取得したactivation・Tool結果・usageと欠測、`ExecutionTrace`/oracleへの変換損失である。`RunObservation`はウェーブ管理記録であり、実Runtime Traceやoracleの入力ではない。合成oracleのPASSを実測に転用しない。

**P1実行はHOLD**。Operator候補環境の版・設定正本、F0/F1配置先、Tool拒否と独立Evidence取得方法をread-onlyで確認するまで、実モデル実行・新Runner/Schema/依存追加は行わない。

### P0 Operator向け引継ぎ（2026-11-17、未実施）

Operatorの候補端末で、**モデルを起動せず**目安100分（最大2時間で中断）で次を確認する。
この管理作業環境で確認したCLI版やfeature表示をOperator実機の結果として転記しない。
最初に`git rev-parse --show-toplevel`を手元だけで確認し、Owner/Operatorが指定した
DAT checkoutのrootであることを照合する。異なるリポジトリならSTOPし、パスは公開しない。
`git rev-parse HEAD`はそのrootで実行し、対象branchとPRの期待HEADも別途照合する。

```sh
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
```

Runtime別のversion/feature/help確認コマンドは上記Adapterを参照する。モデルの実行・権限の負側probe・有料実行は、このread-only手順に**含めない**。未インストール・未対応の項目はUNKNOWNと記録し、推測でPASSに変えない。実体定義・権限・Trace対応は設定の正本を別途read-onlyで照合し、公開Issue/PRには脱識別結果だけを記録する。

| 記録欄 | P0で残す内容（機密部分は伏せる） | 未記入時の扱い |
| --- | --- | --- |
| 環境・版 | Operator候補端末種別、Runtime/CLI版、対象commit、確認日 | UNKNOWN |
| F0 / F1定義 | 同一配送ETAタスクに対応する専門Subagentとdomain Skillの定義・ロード経路、起動手順。現DATには対になる実体が未整備 | 未整備ならHOLD |
| 実効権限の確認方法 | 親mode、F0/F1のTool allow/deny、workspace・通信境界、拒否を確認する負の試験の計画 | 強制方法不明ならHOLD |
| 独立証拠の確認方法 | activation、Tool入出力、拒否、失敗・再試行、usage、欠測を採取する経路と`ExecutionTrace`/oracleへの変換損失 | 真正性・欠測未確認はNOT_TESTED |
| 実行承認 | Operator、使用Model/Effort、失敗・中断・再試行を含む全legの総額上限、承認済みの非公開証拠保存先、通信先、停止条件、独立Reviewer | 未承認ならP1 HOLD |

共有するのは上記の**脱識別した判定と根拠**のみ。生の認証設定、APIキー、
ユーザー固有パス、AATのprivate資料、生Transcriptを公開Issue/PRへ貼らない。
P0は手段と未確認点の特定までを完了条件とする。F0/F1実activation・同等権限・
Trace完全性は引き続きNOT_TESTEDで、時間内に未解決の前提が残ればHOLDを維持する。
P1はDAT Operator/HOTL承認後にのみ実行する。
