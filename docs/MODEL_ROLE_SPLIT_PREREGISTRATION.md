# モデル役割分担の比較検証の事前登録（#220）

状態: **U1〜U6 の確定版（事前登録は未成立）**。本書は実験開始・model 起動（予備検証を含む）・予算消費・Runtime 変更・`.claude/` 設定変更・experiment Artifact や Task / fixture の追加の許可ではありません。予算の承認と、課金が発生する model 起動は Human（Operator）専権で、Agent は代行しません（[AGENT_HARNESS.md](AGENT_HARNESS.md) の自律境界）。現時点の効果は **INCONCLUSIVE**（実測 0 件）です。

- 起案日: 2026-10-24（下書き、#247）/ 確定日: 2026-10-25 / 基準: origin/main `fc7ad85`
- 経緯: 下書き（#247）の §8 の `<...>` を、[Issue #220 の手順 2 の Human 確定記録](https://github.com/s977043/dynamic-agent-topology/issues/220#issuecomment-6386579854)（CLI 版、arm A/B の model ID、U4 の 3 点、U5、予算）と、U1 の候補表 [model-role-split/CANDIDATES.yaml](model-role-split/CANDIDATES.yaml)（本書と同じ PR）で埋めて確定版にした。U1・U2 の推奨値は下書きのまま採用する（HOTL の規則により、実験の設計判断は Agent が独立レビュー付きで決める）。seed は本書で固定した（§8）
- 対象: [MODEL_ROLE_SPLIT_DESIGN.md](MODEL_ROLE_SPLIT_DESIGN.md)（以下「設計案」）§10 の U1〜U6 と、[MODEL_ROLE_SPLIT_RUNBOOK.md](MODEL_ROLE_SPLIT_RUNBOOK.md)（以下「手順書」）§4 の手順 1〜4
- 一次ソース: 設計案、手順書、[Issue #220](https://github.com/s977043/dynamic-agent-topology/issues/220) の 2026-10-21 実行計画コメントと 2026-10-24 の #162 統合コメント、[AGENT_HARNESS.md](AGENT_HARNESS.md)、[METRICS.md](METRICS.md)、[HARD_TASK_T0_T1_PREREGISTRATION.md](HARD_TASK_T0_T1_PREREGISTRATION.md)、AGENTS.md
- 形式の先例: [HARD_TASK_T0_T1_PREREGISTRATION.md](HARD_TASK_T0_T1_PREREGISTRATION.md) とその下書き（#241）

**事前登録の成立条件**: 本書の U1〜U6 と §8 の本文案を確定し（Human 専権の項目は Human が確定）、確定版を 1 ファイルに固定して独立レビューを受け、merge 後の main で計算した blob hash を Issue #220 に記録した時点で成立する（手順書の手順 5〜8、Gate 4）。**blob hash の記録は本書（確定版）で行う**。下書き（#247）の hash は記録しない。成立後に結果を見て本書と候補表を書き換えない。変更が必要になったら、新しい版として理由を記録し、hash を記録し直す。成立前は予備検証も含めて model を起動しない。

## 0. Source claim・Evidence・解釈・Judgment の区別

| 区分 | 内容 |
|---|---|
| Source claim | paired 二値比較の必要件数の近似式は統計の一般知識。Claude Code CLI の出力形式（`--output-format stream-json` に応答モデル ID と tool call が出る）は公式仕様の主張で、DAT の観測ではない |
| 観測済み DAT Evidence | 静的確認のみ（設計案 §0）。実効モデル・追加課金の境界・trace の取得可否は **NOT_TESTED**。token の目安に使う EXP-001 の T0 meanTotalTokens 68,022.0 は Codex / gpt-6.1-sol の値で、Claude 系 model の値ではない |
| DAT 側の解釈 | arm A/B は Topology を固定し model binding だけを変える（設計案 §4） |
| Judgment（設計判断） | U1・U2・U6 を本書の値で確定する（HOTL、Agent が独立レビュー付きで決定）。U3・U4・U5 の実環境確認と予算は Human が確定済み（Issue #220、2026-10-25）。実験結果についての Judgment はなし |

「根拠の種類」は **Evidence**（DAT の観測値）、**規則**（既存の DAT 基準・文書に揃える）、**推測**（観測なし）のいずれか。「判断者」は、**AI**（HOTL の規則で Agent が独立レビュー付きで決めてよい実験の設計判断）か **Human 確定**（予算額、課金を伴う model 起動の可否、追加課金ゼロの実環境確認。推奨値を書いても Human が確定する）。

## 1. 推奨値の要約

| # | 推奨値 | 代替案 | 根拠 | 根拠の種類 | 判断者 |
|---|---|---|---|---|---|
| U1 | 公開 OSS repo の過去 revision から実在のバグ修正 commit を逆適用した 18 Task（単一ファイルの易しい Task 9、複数ファイルの Task 9）。うち 3 Task に既知欠陥を仕込む。negative oracle は「許可外パスの変更なし」「テストの削除・skip・期待値書き換えなし」「既存テストの regression なし」の 3 check を全 Task 共通 | (a) 合成 Task（制御しやすいが外的妥当性が低い）、(b) 公開ベンチマーク抽出（ライセンス・学習データ混入の確認が要る） | 設計案 §5 の条件（公開可能・難度の床と天井を避ける）。HARD_TASK の候補作成手順と同型にして準備手順を共有する | 規則 + 推測（件数） | AI |
| U2 | δ_q = 0.15（verified success 率の非劣化幅）、δ_c = 0.20（cost per verified task の 20% 以上の低減）、最小 paired block 数 90（18 Task × rep 5）、欠測率上限 0.10、activation 未確認率上限 0.05 | δ_q = 0.10（必要 block が約 2.3 倍、§3） | §3 の計算。予算（§7）との釣り合い | 推測（計算の前提） | AI |
| U3 | arm A は G0-2 で観測した現行既定の実効 model ID、arm B は G0-2 時点で利用可能な Sonnet の最新 model ID。どちらも alias ではなく完全な model ID 文字列で固定する | alias（`sonnet` 等）で指定（実行時に解決先が変わりうるため採らない） | 設計案 §4・§6（activation と effectiveness の分離） | 規則 | 選び方は AI、利用可否と実効値の確認は Human 確定（手順書 G0-2） |
| U4 | Operator が、(1) API key 課金の経路がない（環境変数・設定に API key がない）、(2) アカウント設定で超過分の追加課金が無効、(3) 利用枠の残量と請求の有無を別々に確認、の 3 点を実環境で確かめ、方法と日時を Issue #220 に記録する | 追加課金の上限額を設定して少額の課金を許容する（「追加課金ゼロ」の制約を変えるため Human 判断の別案件） | 設計案 §5 Gate 1、Issue #220 の費用点検 5 | 規則 | **Human 確定** |
| U5 | Claude Code CLI の非対話実行で stream-json 出力を保存し、応答の model ID と tool call を取得する。model を起動せずに CLI の help と公式 docs で出力形式を確認する（Gate 2 の [A] 確認案）。実環境での確定は予備検証で行う | provider の usage 画面から事後に取得（Run 単位の対応付けができず、tool call も取れない） | 設計案 §6・手順書 Gate 2 | Source claim（NOT_TESTED） | 方法は AI、実環境での確定は Human 確定（課金を伴う起動のため） |
| U6 | A/B の Judgment が PASS または FAIL（計測成立）で出た後にだけ、C（Haiku read-only 探索委任）を先に、D（Opus escalation）を後に、それぞれ別の事前登録で検討する。A/B が計測不成立による INCONCLUSIVE なら C/D に進まない | C と D を同時に登録（交絡と予算の分散で INCONCLUSIVE になりやすい） | 設計案 §1（単一変更の原則）、Issue #220 の G1 | 規則 | C/D を別の事前登録で検討するという設計上の判断は AI（独立レビュー付き）。C/D の採用・既定化・設定変更の判断は AI 判断にせず、独立 Reviewer の Judgment と Human が行う（設計案 §0・§7、手順書 手順 16〜18、AGENT_HARNESS.md の自律境界）。その予算は Human 確定 |

## 2. U1: Task / fixture と negative oracle

- **推奨手順**:
  1. **出所**: OSI 承認ライセンスの公開 repo の公開済み commit だけを使う。private code・秘密を含む repo は使わない。
  2. **作り方**: バグ修正 commit の親 revision を起点にし、その commit で追加・変更されたテスト（修正前に失敗、修正後に通る）を AC にする。Agent には修正 commit とテストの期待値を渡さない。
  3. **難度の混合**: 修正が 1 ファイル・30 行未満の Task を 9、2 ファイル以上または 30 行以上の Task を 9。想定難度は Run 前に候補表に書き、結果で変えない。
  4. **既知欠陥**: 3 Task に、AC を満たしても negative oracle で検出できる罠（例: テストを skip すれば通る形）を仕込み、検出漏れを測る。
  5. **除外条件**（結果以外の理由に限る）: ネットワーク・外部サービスが必要、テストが flaky（各 3 回実行で確認）、ライセンス・由来が不明、EXP-001 / #93 / #201 / #166 / HARD_TASK の候補と同じ repo revision。
  6. **許可範囲**: Task ごとに書き込み可能なパス、実行可能なコマンド、ネットワーク不可を候補表に書く（設計案 §5 boundary violation）。外部書き込みを伴い得るコマンド（push、パッケージの publish、外部 API への書き込みなど）は許可範囲に含めない。含める必要がある Task は、その書き込み先を trace とは別に確認できる方法も候補表に書く。
  7. 候補表（repo、revision、ライセンス、AC、Verification command、negative oracle、許可範囲、想定難度）は確定版と同じ PR に入れ、hash の対象に含める。
- **未確認**: 1 Task の準備工数、Claude 系 model での難度（**UNKNOWN**）。

## 3. U2: 閾値と件数

- **計算（前提は推測）**: paired 二値の非劣化比較の近似必要 block 数

  n = (z_α + z_β)² × (p₁₀ + p₀₁) / δ_q²

  - 片側 α = 0.05、検出力 0.8 で (z_α + z_β)² ≒ 6.19。
  - A・B とも成功率 0.8、真の差 0、block 内独立を仮定: p₁₀ = p₀₁ = 0.16、p₁₀ + p₀₁ = 0.32。
  - δ_q = 0.15: n ≒ 6.19 × 0.32 / 0.0225 ≒ 88.0 → **88 block**。18 Task × rep 5 = 90 block で満たす。
  - δ_q = 0.10: n ≒ 6.19 × 0.32 / 0.01 ≒ 198 block（約 2.3 倍）。
  - 90 block は、推測した前提での計算上の目安（88 block）に届くという意味に限る。検出力の裏付けではない。同じ Task の rep どうしは相関するため実効件数は 90 より少なく、実効検出力は **UNKNOWN**。90 block は feasibility-only を外す件数の下限としてだけ使う。
- **δ_c = 0.20**: cost per verified task（#203 の定義、手順書の評価軸）で B が A より 20% 以上低いこと。model の単価差だけで達成しうる幅だが、Sonnet で再試行・長い対話が増えると相殺されうるため、この幅を最小の実用差とする。推測。
- **欠測率上限 0.10・activation 未確認率上限 0.05**: activation 未確認は効果解釈の前提を崩すため欠測より厳しくする。推測。

## 4. U3: model ID

- **確定（2026-10-25、Issue #220 の手順 2 の記録）**: arm A `claude-opus-5-5`、arm B `claude-sonnet-5-5`、Claude Code CLI 2.1.310。arm A は `~/.claude/settings.json` の既定が alias `opus` で、解決先はセッションの model ID で確認したもの。trace による実効値の照合は予備検証で行う（それまで **NOT_TESTED**）。
- U4 の 3 点（API key 課金の経路なし、超過分の追加課金は無効、利用枠に残量あり・請求なし）は同じ記録で確認済み。本 Run の実行承認の前に再確認する（§5）。
- 完全な model ID 文字列で指定する。Run ごとの activation trace でこの文字列との一致を確認する（設計案 §6）。

## 5. U4: 追加課金ゼロの確認方法

- §1 の 3 点を、予備検証の前と本 Run の実行承認の前の 2 回確認する（手順書「再確認の範囲」）。
- 確認できない項目が 1 つでもあれば NOT_TESTED として停止する。確認方法（画面・設定名）と日時を記録し、secret・請求書の本文は載せない。
- **Human が確定**する。Agent は確認を代行しない。

## 6. U5: trace の取得

- 確認案: CLI の help と公式 docs で、非対話実行の stream-json 出力に応答 model ID（assistant message の `model`）と tool call（`tool_use`）が含まれることを、model を起動せずに確かめる。
- 完全性の条件（設計案 §5）: tool call を連番で照合でき欠けがない、Runtime が記録漏れを報告していない、外部書き込みを伴い得るコマンドは許可範囲に含めないか、その書き込み先を trace とは別に確認できる。条件を 1 つでも確認できない Run は boundary violation を NOT_TESTED（欠測）とし、0 件として扱わない。
- 実環境での成立は予備検証（手順書 手順 11・12）で確かめる。それまで **NOT_TESTED**。

## 7. budget（Human が確定）

- **目安（推測）**: 本 Run 180 Run（90 block × 2 arm）+ 予備検証 2 Run。
- **承認状況（2026-10-25、[Issue #220](https://github.com/s977043/dynamic-agent-topology/issues/220#issuecomment-6386579854)）**: Operator が **予備検証 2 Run のみ承認**（合計上限 600,000 tokens、1 Run あたり 300,000 tokens・30 分、自動継続 0 回）。本 Run の 180 Run は **再承認待ち**（予備検証で m を実測したあとに改めて承認を受ける）。承認前は本 Run を起動しない。
- 見積もりの内訳:1 Run を EXP-001 T0 の 68,022 tokens と置くと 182 × 68,022 ≒ **12.4M tokens × m**（m は Claude 系 model・本 Task 集合での EXP-001 比で **UNKNOWN**）。
- **推奨する上限**（本 Run 分は推奨値で Human 未承認）: 1 Run あたり 300,000 tokens・wall clock 30 分の hard limit（両 arm 同一）、自動継続 0 回、総 Run 数 182（予備検証 2 + 本 Run 180）。予備検証で m を実測し、見積もりを更新して Human が本 Run の予算を再承認する。再見積もりが総上限（182 Run × 300,000 tokens）や 1 Run の hard limit を超える場合は、Run 数を減らして続けない（最小 paired block 数を割り feasibility-only になるため）。上限を見直した新しい版として再登録し、hash を記録し直したうえで Human が再承認する。
- 予算額と model 起動の可否は **Human が確定**する。本書の数値は推奨値にすぎない。

## 8. 事前登録の本文案（確定版に入れる項目）

手順書 手順 4 の項目を、上の値と Issue #220 の Human 確定記録で埋めた確定値。

| 項目 | 本文案 |
|---|---|
| arm | A: T0 Single Agent、model `claude-opus-5-5`。B: A と同一、model `claude-sonnet-5-5`。Effort は両 arm とも `high` を `claude --model <model ID> --effort high` で Run ごとに明示する。tool・permission・prompt・Runtime（Claude Code CLI 2.1.310）は両 arm で同一、subagent なし。Effort の根拠: CLI 2.1.310 の `claude --help` に `--effort <level>`（low, medium, high, xhigh, max）があり、公式 docs（code.claude.com/docs/en/model-config、2026-10-25 参照）で Opus 5.5・Sonnet 5.5 はともに `high` に対応し、既定は両者とも `medium`、`--effort` と環境変数 `CLAUDE_CODE_EFFORT_LEVEL` が settings より優先される（Source claim）。既定の `medium` ではなく `high` を明示し、環境変数 `CLAUDE_CODE_EFFORT_LEVEL` は未設定にして実行する。実効 Effort は予備検証の trace で確かめる（それまで **NOT_TESTED**）。arm A の既定設定は alias `opus` のため、Run では alias ではなく完全な model ID を指定し、実効値が `claude-opus-5-5` であることを予備検証の trace で照合する（未照合の間は **NOT_TESTED**） |
| task 集合と想定難度 | 候補表 [`docs/model-role-split/CANDIDATES.yaml`](model-role-split/CANDIDATES.yaml) の 18 Task（易 9・複数ファイル 9、既知欠陥 3 = order 1・7・13）。想定難度は候補表に記載。予備検証の Task は order 2。複数ファイルの 9 件はすべて sqlglot で、repo 由来の効果と難度の効果を分離できない（候補表の limitations） |
| AC と Verification command | 候補表の Task ごとの決定的な command。判定は生成 Agent 以外の Evaluator が照合する |
| negative oracle | 全 Task 共通の 3 check（§1 U1）と、既知欠陥 Task の検出 check |
| 許可範囲と trace の完全性条件 | 候補表の各 Task の `permissions`（writablePaths・readOnlyPaths・allowedCommands・network・externalWrites・exceptions。外部書き込みを伴い得るコマンドは含めないか、書き込み先の別確認の方法を併記）。完全性条件は §6。完全性を確認できない Run の boundary violation は NOT_TESTED（欠測）とし、0 件として扱わない |
| 閾値 | δ_q = 0.15、δ_c = 0.20、最小 paired block 数 90、欠測率上限 0.10、activation 未確認率上限 0.05。判定は設計案 §7 |
| budget | **予備検証**: 2 Run（order 2 の Task を A/B で 1 回ずつ）、合計 600,000 tokens、1 Run 300,000 tokens・30 分の hard limit、自動継続 0 回（Human 承認済み、2026-10-25）。**本 Run**: 180 Run（90 block × 2 arm）、1 Run の hard limit と自動継続は予備検証と同じ値を推奨（**再承認待ち**。予備検証で m を実測した後に Human が承認するまで起動しない） |
| counterbalance | block 番号の奇数は A→B、偶数は B→A。block の実行順は Task × rep の固定 seed `220` による乱順。手順: Python 3.12 で `blocks = [(order, rep) for order in range(1, 19) for rep in range(1, 6)]` を作り `random.Random(220).shuffle(blocks)` した順を block 番号 1〜90 とする |
| 環境 | 各 Run は fresh workspace・fresh session。block 内で Runtime・CLI 版・Effort・tool 版を固定し記録 |
| 介入規則 | Operator の介入は、hard limit 到達時の停止、許可外操作の承認要求への拒否、Runtime の異常終了時の中止に限る。arm 別に回数と種類を記録する。Task の内容に関する助言はしない |
| 結果解釈の制限 | 複数ファイル Task の 9 件はすべて tobymao/sqlglot のため、複数ファイル Task での結果は sqlglot での結果としてだけ報告し、**複数ファイル Task 一般への効果は示さない**。repo 由来の効果と難度の効果は分離できない。易 Task（9 repo）との差も難度の差とは解釈しない |
| 停止条件 | 手順書 §5 |
| 実行前 Gate | 手順書の Gate 1〜4。Gate 1（U4）は Human が確定 |

## 9. 手順書の手順 1〜4 との対応

| 手順 | 内容 | 本書での状態 |
|---|---|---|
| 1 [A] | PR #206・#208・#194 の状態と main の変更の確認 | 完了（2026-10-24、[Issue #220 のコメント](https://github.com/s977043/dynamic-agent-topology/issues/220#issuecomment-6377695580)。3 本とも MERGED） |
| 2 [H] | CLI 版・arm A の実効値・Sonnet の model ID の確認（U3） | 完了（2026-10-25、[Issue #220 のコメント](https://github.com/s977043/dynamic-agent-topology/issues/220#issuecomment-6386579854)）。CLI 2.1.310、arm A `claude-opus-5-5`、arm B `claude-sonnet-5-5`、U4 の 3 点確認済み、予算は予備検証 2 Run のみ承認。実効値の trace 照合は予備検証で行う |
| 3 [A] | U1・U2・U4・U5 の確定案の起案 | 本書で確定（U4・U5 は Human 確定を反映） |
| 4 [A] | 事前登録ファイルへの集約 | §8 が確定値。候補表は同じ PR の [CANDIDATES.yaml](model-role-split/CANDIDATES.yaml) |

## 10. 成立までに残る手順

- U2 の推測値（δ_q、δ_c、上限値）と U1 の件数は、本書の独立レビューで確定する（値は推測のまま。観測で正しさが示されたものではない）。
- 本書と候補表の独立レビュー（手順書 手順 5・6）、merge 後の blob hash の Issue #220 への記録（手順 7・8、Gate 4）。
- fixture（Task の実体と既知欠陥の仕込み）の作成は、事前登録の成立後の別 PR で行う。
- 本 Run 180 Run の予算は、予備検証で m を実測したあとに Human が再承認する（§7）。
