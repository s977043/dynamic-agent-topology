# EXP-001 Codex Pilot Runbook

## 目的

EXP-001の最初のPilotとして、**T0 Single Agent vs T1 Worker + Verifier** をCodex単一Runtimeで比較します。

これは性能結論を出す本試験ではなく、Run contract / Trace / Evaluation / paired comparison /集計が実Runtimeで成立するかを確認するPilotです。

## 固定条件

- Runtime: `codex`
- Model: `gpt-6.1-sol`
- Effort: `high`
- Conditions: `T0`, `T1`
- Scenarios: train / test / regression 各1
- Repetitions: 3
- Total runs: 18
- Fresh workspace: runごとに必須
- Fresh Codex session/context: runごとに必須
- Cross-run feedback: 全18 Run完了まで禁止
- Order: paired block内でT0/T1の先行条件をcounterbalance

Pilot条件の正本は [pilot.yaml](pilot.yaml)、Run一覧は [run-matrix.yaml](run-matrix.yaml) です。

## 実行前チェック

1. Codexの実セッションでmodel / effortを確認する。
2. runごとにfresh Codex session/contextを開始する。前Runの会話履歴を再利用しない。
3. fresh workspaceを作成する。
4. 対象fixtureをfresh workspaceへコピーする。
5. 初期Evidenceが失敗することを確認する。
6. 対象Runの `runId` / `blockId` / condition / `executionOrder` をrun-matrixから取得する。
7. matrixの順番どおりにpaired blockを実行する。
8. T0とT1の同じblockではRuntime / Model / Effortを変更しない。
9. 全18 Runが完了するまで、先行Runの評価結果を後続RunのPrompt/Role/設定改善に使わない。

## T0

T0はSingle Agentです。

- 1 AgentだけでTaskを実装する。
- Verifier subagentを起動しない。
- 実装後にScenarioのdeterministic Evidenceを取得する。
- Agent自身の「大丈夫」という判断ではなくEvidence結果をRunEvaluationへ記録する。

## T1

T1はWorker + independent Verifierです。

- Workerが実装する。
- VerifierはWorkerと分離したRole/contextで確認する。
- Verifierは実装を修正しない。修正が必要ならWorkerへ戻す。
- 最終判定はdeterministic Evidenceを優先する。
- VerifierがPASSしたのにEvidenceがFAILなら `verifierFalseAccept: true` とする。

Codexのcustom roles / subagent model / effortはRuntime設定で固定し、Run途中で変更しません。

## 保存Artifact

各Runは次のディレクトリに保存します。

```text
runs/pilot-codex/<runId>/
├── run-meta.yaml
├── prompt.md
├── trace.yaml
├── evaluation.yaml
├── patch.diff
└── evidence.txt
```

### tracked

- `run-meta.yaml`
- `prompt.md`
- `trace.yaml`
- `evaluation.yaml`
- `patch.diff`
- `evidence.txt`

### 保存しないもの

- API key / token
- 認証情報
- private environment dump
- chain-of-thought / hidden reasoning
- unrelated user/repository data

## Run完了判定

Runは以下を満たすまでcompleteではありません。

- run-meta/trace/evaluationがSchema valid
- runId / blockId / scenario / conditionがmatrixと一致
- deterministic Evidence結果が記録済み
- patchが保存済み
- `run-meta.yaml` でfresh workspace / fresh session / cross-run feedback未使用を記録する
- workspaceId / sessionId は18 Run間で一意にする（秘密情報ではなくRun用opaque IDを使う）
- workspaceはDAT repository外に置く
- prompt.mdはrun-meta.yamlのpromptSha256と一致する
- T0/T1 paired blockのRuntime / Model / Effortが一致

## Pilot完了判定

18 Runすべて完了後:

```bash
python scripts/validate_pilot.py \
  --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml \
  --require-complete
```

その後 `scripts/summarize_experiment.py` で集計し、`DECISION.md` を更新します。

**18 Runが揃う前にT0/T1の優劣を判断せず、途中結果を後続Runへフィードバックしません。**


## Operator Kit

18 Runを手作業で直接組み立てず、[OPERATOR.md](OPERATOR.md) の手順で `prepare_pilot_run.py` / `pilot_status.py` を使用します。

Operator KitはCodexを起動せず、fresh fixture / run-meta /固定Prompt /進捗だけを管理します。実測結果は実Runtime実行後に保存します。
