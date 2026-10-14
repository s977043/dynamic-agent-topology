# Provenance監査の再現と設計案（#57）

状態: **非規範的な設計案（未採用）**。この文書は検査の穴の再現と、独立auditの最小案の比較だけを扱います。validatorの実装、Schemaの変更、EXP-001の評価意味論の変更は含みません。EXP-001の18 Runの受理判断と [DECISION.md](../experiments/EXP-001-t0-vs-t1/DECISION.md) は、この文書によって変わりません。

関連: [Issue #57](https://github.com/s977043/dynamic-agent-topology/issues/57)、[CURRENT_EXECUTION_PLAN.md](CURRENT_EXECUTION_PLAN.md) 優先順1、研究候補 H1（[production-agent-capabilities-dat-evaluation-2026-10.md](../knowledge/research/production-agent-capabilities-dat-evaluation-2026-10.md)。採用済みの契約ではない）。

## 実装の統合状況（PR #188、受理ゲートから独立）

[PR #188](https://github.com/s977043/dynamic-agent-topology/pull/188) は、独立レビューと必須CI成功後に `2e1d9e6` でmerge済みです。案Bの非規範的な読み取り専用監査であり、採用済み規範や原本独立性を意味しません。[運用評価](PROVENANCE_AUDIT_OPERATIONS.md)に検出範囲・実行コスト・残条件を記録しています。以下の設計時の「別PR」「実装する場合」は実装前の履歴です。

- `python scripts/audit_provenance.py --run-dir fixtures/provenance-audit/baseline-consistent/runs/EXP-001-train-normalize-name-r01-T0`
- `python scripts/audit_provenance.py --runs-root experiments/EXP-001-t0-vs-t1/runs/pilot-codex`
- `python scripts/test_audit_provenance.py`（合成Fixture、観測欠落、過去18 Runのread-only照合）

標準出力には**関係単位**の PASS / FAIL / UNKNOWN と**Run単位**の総合判定を出します。FAILが1件以上ならprocess exit 1、UNKNOWNだけならexit 0ですがUNKNOWNは明示表示し、成功・Attestation保証と数えません。このコマンドは `validate_pilot.py` の受理ルールを変更せず、古いRunへの照合は報告用途のみです。元の18 Runの再実行・Run Artifactの変更は行いません。

監査項目は metadata、runtime/model/effort、session/fresh/cross-run、start/finish時刻（タイムゾーン表記を正規化）、input/output tokens、wallclockです。一致は**記録値同士の整合**に過ぎず、真正なRuntimeログ・Permission Enforcerの独立証明ではありません。Attestation原本の偽造、観測されない副作用、許可違反をこの監査で発見できるとは主張しません。

## 1. 観測した事実

### 1.1 現行の検査範囲（`scripts/validate_pilot.py`、main 24fa06b）

Run Artifact単位で、次の関係を検査しています。

| 関係 | 検査している項目 |
|---|---|
| matrix ↔ 各Artifact | `runId` / `blockId` / `scenario` / `condition` |
| pilot ↔ Attestation / Trace / Evaluation | `runtime` / `model` / `effort` |
| Attestation ↔ Trace / Evaluation | `runtime` / `model` / `effort` |
| Attestation単体 | `freshSession: true`、`crossRunFeedbackUsed: false`、`finishedAt > startedAt`、`sessionId` のRun間重複 |
| Trace ↔ Evaluation | `agentInvocations` / `coordinationTransitions` / `wallClockMs`（Trace側にfieldがあるときだけ）、`humanInterventions` |

次の関係は検査していません（Issue #57 の Candidate checks）。

- Trace start eventの `details.sessionId` / `freshSession` / `crossRunFeedbackUsed` ↔ Attestation
- Trace start / finishの `timestamp` ↔ Attestation `startedAt` / `finishedAt`
- Trace `summary.inputTokens` / `outputTokens` ↔ Evaluation `efficiency`
- Trace `summary` にfieldがないとき、Evaluation側の値の扱い（現状は比較を飛ばしてPASS扱いになる）

### 1.2 負側fixtureによる再現

[fixtures/provenance-audit/](../fixtures/provenance-audit/README.md) に合成fixtureを置き、既存の `validate_pilot.py --run-id` をPython 3.12で実行しました。

| ケース | exit | 解釈 |
|---|---|---|
| `baseline-consistent` | 0 | 対照（整合） |
| `ctl-trace-model-mismatch` | 1 | 既存の検査に届いている対照 |
| `neg-session-id-mismatch` | 0 | 穴 |
| `neg-fresh-session-mismatch` | 0 | 穴 |
| `neg-timestamp-mismatch` | 0 | 穴 |
| `neg-token-mismatch` | 0 | 穴 |
| `neg-token-field-missing` | 0 | 穴（観測できない値がPASSに化ける） |
| `neg-wallclock-field-missing` | 0 | 穴（観測できない値がPASSに化ける） |
| `neg-trace-session-unknown` | 0 | 穴（観測できない値がPASSに化ける） |

7件の負側ケースがすべて現行のvalidatorを通過しました。各ケースは `baseline-consistent` との差分で1つの関係だけを壊しています（差分の要旨はfixtureのREADME）。これが #57 の再現です。

### 1.3 既存18 Runに対する読み取り専用の照合（参考）

使い捨てのscript（commitしていない）で、`experiments/EXP-001-t0-vs-t1/runs/pilot-codex/` の18 Runを読み取りだけで照合しました。

| 関係 | 結果 |
|---|---|
| Trace start eventの数 / finish eventの数 | 18/18で各1件 |
| `sessionId` / `freshSession` / `crossRunFeedbackUsed` | 18/18で一致 |
| `inputTokens` / `outputTokens` | 18/18で一致 |
| 時刻（文字列の完全一致） | 1/18で一致。17件はUTC offsetの表記だけが異なる（Trace `+00:00`、Attestation `+0000`） |
| 時刻（`datetime.fromisoformat` で解釈した時点の一致、3.12） | 18/18で一致 |

この結果から言えるのは「記録された値どうしが矛盾していない」ことだけです。AttestationはOperatorが `attest_pilot_run.py` にsessionIdや時刻を渡して作る自己申告で、Traceも同じCapture sequence（[EXP-001_ARTIFACT_CAPTURE.md](EXP-001_ARTIFACT_CAPTURE.md)）の中で観測事実から作られます。両者の一致は独立Verificationではありません（Attestation ≠ Verification、[ARCHITECTURE.md](ARCHITECTURE.md)）。また、この照合は上の4関係しか見ていないので、「18 Runにprovenance違反はゼロ」とは主張しません。

時刻を文字列で比べると17件を誤って不一致にします。時刻は時点として比べ、解釈できない値はUNKNOWNにする必要があります。

## 2. 判定の意味

監査は関係ごとに次の3値を返します。

| 判定 | 条件 |
|---|---|
| PASS | 両側に値があり、一致する |
| FAIL | 両側に値があり、一致しない |
| UNKNOWN | どちらかの値がない、解釈できない、または対応が一意に決まらない（start eventが複数あるなど） |

Run全体の判定は、FAILが1つでもあればFAIL、なければUNKNOWNが1つでもあればUNKNOWN、すべてPASSのときだけPASSです。報告では関係ごとの件数を出し、UNKNOWNを0件やPASSとして数えません。UNKNOWNが残るRunについて「違反ゼロ」とは書きません。

旧Experiment（EXP-001）のRunに監査を当てる場合、結果は**報告のみ**とし、既存の受理判断・`verdict`・集計を書き換えません。

## 3. 案の比較

| 観点 | 案A: canonical validatorを拡張 | 案B: 独立した読み取り専用audit | 案C: Schemaで必須化・制約追加 |
|---|---|---|---|
| 内容 | `validate_pilot.py` に4関係の比較を足す | `scripts/audit_provenance.py`（仮）を新設し、関係ごとにPASS / FAIL / UNKNOWNを出す。fixtureのテストをspec-lintに組み込む | Trace start eventの `details` やsummaryのtoken fieldを必須にする |
| 関係ごとの判定値（1.2の7件） | 報告にPASS / FAIL / UNKNOWNを出すように拡張すれば、7件とも区別できる | 7件とも区別できる | 欠落の3件だけ（schema errorとして）。ファイル間の不一致は表現できない |
| process の exit code | 既存の受理ゲート（0 = 受理可）と共用になる。UNKNOWNをexit 0と1のどちらにするかを決めた時点で、EXP-001の受理に使ったゲートの意味が変わる | 受理ゲートとは別に決められる（例: FAILで1、UNKNOWNは報告のみで0）。旧Runへの適用では受理に影響しない | schema errorで1。UNKNOWNとFAILの区別はない |
| 旧Experimentの意味論 | `validate_pilot.py` はEXP-001の受理に使った検査なので、変えると過去の受理基準を事後に変えることになる | 変えない（別のscriptで、旧Runには報告のみ） | 既存Artifactがschema違反になりうる。versioningが要る |
| 変更の大きさ | 小 | 中（script、テスト、spec-lint） | 中（schema、既存Artifactの扱い） |
| Plane境界 | Evaluation Planeの受理検査にaudit責務が混ざる | Observed Execution ↔ Evaluationの照合を独立した層に置ける | Schemaは単一ファイルの形の契約で、ファイル間の関係は扱えない |

推奨は**案B**です。判定値の表現力だけなら案Aでも同じことができます。案Bを選ぶ理由は、`validate_pilot.py` の受理の意味（exit codeを含む）を変えずに、関係ごとの判定を別の層で報告できることです（判断基準: 要件適合性 → 安全性 → 保守性）。案Cの一部（新しいExperimentでのtoken fieldの必須化）は、案Bの観測結果を見てから別に提案します。

案Bでは新しいArtifact kindを作りません。出力はstdoutの報告だけにします。結果をファイルとして保存する必要が出たら、そのときにschemaとsemantic checkを足します（AGENTS.md の新Artifact kindのルール）。

## 4. 反証可能な仮説と検証計画（案Bを実装する場合）

**仮説:** 案Bのauditは、`fixtures/provenance-audit/` の負側7件のうち不一致の4件をFAIL、欠落の3件（`neg-token-field-missing` / `neg-wallclock-field-missing` / `neg-trace-session-unknown`）をUNKNOWNと判定し、対照（`baseline-consistent`）と既存18 Runをいずれも誤ってFAILにしない。

**反証条件（どれか1つで仮説を棄却）:**

- 負側ケースのどれかがPASSになる
- 欠落ケースがPASSまたはFAILになる（UNKNOWNにならない）
- `baseline-consistent` または既存18 Runのどれかが、表記の違い（UTC offsetなど）だけでFAILになる

**期待する観測:** 負側4件がFAIL、欠落3件がUNKNOWN、対照がPASS。既存18 Runは1.3の結果から4関係ともPASSと予想しますが、実装後に実測して確かめます。

**負のテスト:** 1.2の負の7ケースをテストの入力にし、期待判定をテスト側に持つ。加えて、start eventが複数あるケース（UNKNOWN）と、時刻が解釈できないケース（UNKNOWN）を追加する。

**rollback:** auditは独立したscriptで、既存の検査・Artifact・受理判断に依存されないので、scriptとspec-lintのstepを外せば元に戻ります。fixtureは合成で、他から参照されていません。

**採用しない条件:** 既存の検査や手動レビューのテンプレート（`.github/pull_request_template.md` の Cross-artifact consistency review）で十分と判断される場合は、新しい仕組みを足しません（H1のdecision ruleに合わせる）。

## 5. この文書で決めないこと

- 案Bの実装とspec-lintへの組み込み（別PRで、独立レビューを経て行う）
- 新しいExperimentでのSchemaの必須化
- Attestationの出所を独立に検証する手段（runtimeログの原本照合など）。現在のAttestationとTraceは同じCapture sequenceで作られるため、一致してもforgeryは検出できません。H1の「forged attestation」ケースは、この層では検出できないと明記して残します。
