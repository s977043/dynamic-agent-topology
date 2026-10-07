# EXP-001 Operator Kit

Operator KitはCodexを自動実行しません。18 Runの**準備・順序・provenance・進捗**をDAT側で統制します。

## 1. 次Runを確認

```bash
python scripts/pilot_status.py \
  --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml
```

`executionOrder` はpaired block内の先行条件です。matrixの順序を変更しません。

## 2. Runを準備

例:

```bash
python scripts/prepare_pilot_run.py \
  --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml \
  --run-id EXP-001-train-normalize-name-r01-T0 \
  --workspace /tmp/dat-exp001-r01-t0 \
  --workspace-id exp001-r01-t0-workspace
```

条件:

- `--workspace` は存在していてはいけません。
- `--workspace` はDAT repositoryの外側に置きます。これによりCodex sessionから他Run Artifactへ親ディレクトリ経由で到達しにくくします。
- workspace IDはPilot内で一意な**非秘密のopaque ID**にします。
- providerのtoken、API key、private path等をIDへ入れません。
- **通常Run**では同じrunIdを再prepareしません。中断・失敗attemptは消さず、個別のreviewed dispositionなしに同じslotを再実行しません。`EXP-001-train-normalize-name-r01-T1` に限り、[#97で承認されたone-time retry](../../../docs/EXP-001_RETRY_T1_R01.md) に従ってoriginal archiveを保全・照合し、normal sandboxで凍結Evidence commandのnative起動と初期Evidence FAILを確認した場合だけ、**frozen planを変更せず**同じslotをfresh workspace / session向けにreprepareできます。retry allowanceはpreflight・reprepareでは消費せず、fresh Codex **model invocation開始時**に消費します。それ以外のRunにこの例外を流用しません。
- `prompt.md` のSHA-256を `run-meta.yaml` に保存し、完了検証時にPrompt改変を検出します。

生成物:

```text
workspace/
└── fixtureのfresh copy

runs/pilot-codex/<runId>/
├── run-meta.yaml
└── prompt.md
```

ここでは結果Artifactを生成しません。

## 3. Codexを実行

`prepared` はGit管理されたmetadata / Promptの存在を示すだけで、現在のOperator hostに実workspaceが存在することは保証しません。開始前に、prepareが生成したworkspaceへアクセスでき、凍結fixtureのfresh copyであることを確認します。

### First T0の実測前workspace復旧 — #48

`EXP-001-train-normalize-name-r01-T0` は #25 / #32 の一時的なGitHub Actions runner上でprepareされました。runner外にworkspaceが引き継がれていないため、#48で追跡する**このRunだけの実測前インフラ復旧**を、再prepare禁止の例外として扱います。

復旧は、この例外を記載したPRの独立レビュー・merge後にのみ実施します。#15と #32 が記録する実測未開始を根拠とし、操作者が過去のempirical invocationを発見した場合、または未開始を確認できない場合は停止します。結果ファイルの不在だけを未開始の証明にしません。

1. 元のrun directory全体をDAT checkout / artifactRoot / 実測workspaceの外へ退避し、2つの準備ファイルのhashと旧workspaceIdを保存する。既存の作業checkoutには手を加えず、clean isolated checkoutを使う。
2. 他の既存・退避済みworkspaceIdと異なる新ID、DAT checkout外の存在しないworkspace pathを指定し、凍結済み `prepare_pilot_run.py` を変更せず実行する。
3. 生成Promptが退避した原本とbyte単位で一致し、YAML metadataが `spec.workspaceId` 以外同一であることを確認する。生成workspaceと凍結fixtureのファイル内容一致、Feature Freeze validationも確認する。
4. #48に対応するGit管理文書へ、元prepareのPR / workflow、実測未開始の記録、旧・新workspaceId、hash、比較結果を保存し、準備差分をレビューする。その後、通常の初期Evidence FAIL確認とfresh Codex session実行へ進む。

失敗時は部分生成物を隔離して保存し、退避した元のrun directoryを復元します。自動で復旧を再試行しません。この例外は実測済み / aborted / infrastructure-failed sessionの再実行、結果Artifactの置換、他Runの再prepareには使いません。復旧だけでexecution attestationや実測値を生成しません。

### T1 r01 infrastructure retry — #97

`EXP-001-train-normalize-name-r01-T1` のexit 127による不完全attemptには、[#97でレビューされたT1 r01 one-time retry procedure](../../../docs/EXP-001_RETRY_T1_R01.md) を、**その手順のPRがmergeされた後に限り**適用できます。

これは通常の `ACCEPT` gateを緩めるものではありません。元attemptは永久保存し、normal experimental sandboxで凍結Evidence commandが起動可能であることを非model preflightで確認した後、一度だけfresh retryします。retry allowanceはmodel invocation開始時に消費され、結果に関係なく再々試行は許可しません。

### 通常の実行手順

#51の最初のT0には、[限定再試行手順](../../../docs/EXP-001_RETRY_51.md)を適用できます。これは #48 の実測前復旧とは別の例外で、元の実セッションを保存し、手順の独立レビュー・merge後に一度だけ再試行します。他のRunやtask failureには適用しません。

1. fresh workspaceでScenarioの初期deterministic Evidenceが失敗することを確認する。初期状態でPASSする場合はRunを開始せず、#15で停止理由を記録する。
2. 新しいCodex session/contextを開始する。
3. 対象Runの `prompt.md` だけを入力として使う。
4. Run開始時点を記録し、終了時点との差分から `wallClockMs` を実測する。
5. 他RunのArtifact/結果を参照しない。
6. T0/T1のRole Contractを変更しない。
7. Run終了後、実際に観測したsession/runtime事実を `execution-attestation.yaml` として記録する。
8. Trace / Evaluation / patch / Evidenceを保存する。

### 実行後Attestation

実Codex session終了後、preparation時の予定値ではなく**実際に観測した値**を記録します。

```bash
python scripts/attest_pilot_run.py \
  --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml \
  --run-id <runId> \
  --session-id <actual-opaque-session-id> \
  --fresh-session true \
  --cross-run-feedback-used false \
  --runtime codex \
  --model gpt-6.1-sol \
  --effort high \
  --started-at <ISO8601-with-timezone> \
  --finished-at <ISO8601-with-timezone>
```

`fresh-session` や `cross-run-feedback-used` は期待値へ合わせて書き換えません。汚染があったなら実際の値を記録し、validatorにinvalid判定させます。

## 4. 進捗状態

`pilot_status.py` は次だけを表示します。

- `planned`: 未準備
- `prepared`: run-meta + promptのみ
- `in-progress`: 結果Artifactが一部存在
- `artifacts-present`: 必要ファイルは存在しnon-empty
- `invalid`: preparation/result file setが不正

**artifacts-present ≠ complete** です。

各Run終了後は、そのRunだけをsemantic validationします。

```bash
python scripts/validate_pilot.py \
  --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml \
  --run-id <runId>
```

このsingle-run validationがPASSすることは必要条件ですが、それだけでRun acceptanceは完了しません。

結果PR本文のObservable Evidenceと差分をReviewerが確認し、review commentに `EXP-001 Run acceptance: ACCEPT` が記録されるまで次のmatrix itemへ進みません。validation PASSはArtifact contract整合、`ACCEPT` はそのRunをcomplete empirical Runとして受理できるというReviewer Judgmentです。Condition / Topologyの優劣判断ではありません。

18 Runすべての最終completionは:

```bash
python scripts/validate_pilot.py \
  --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml \
  --require-complete
```

で判定します。
