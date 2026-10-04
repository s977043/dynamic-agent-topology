# Engineering Layer Diagnostics

DATのArchitecture Planeは**責務を分離するための構造**です。一方、この文書のEngineering Layerは、失敗が起きたときに**どこを直すべきかを診断するためのレンズ**です。

この2つを同じ階層モデルとして扱いません。

- Architecture Plane: Desired Organization / Control Plane / Runtime Mapping / Observed Execution / Evaluation
- Engineering Layer: Prompt / Context / Harness / Loop / Graph / Evaluation

Engineering Layerは成熟度順でも依存順でもありません。複数Layerにまたがる失敗もあります。

## Diagnostic layers

| Layer | 診断対象 | DATで主に対応する概念 |
|---|---|---|
| Prompt | 指示、Roleの責務、Task contractが曖昧・矛盾していないか | Role Contract, task/prompt contract |
| Context | 判断に必要な情報、Artifact、handoffが欠落・汚染していないか | Context Boundary, handoff artifact, project binding |
| Harness | 実際のCapability、Permission、Tool、CI、Evidence取得経路が意図どおりか | Permission Boundary, Runtime Adapter, Evidence binding, validator |
| Loop | Retry、停止条件、Budget、Escalation、状態遷移が制御されているか | Routing / Escalation policy, execution state |
| Graph | Node / Edge / Dependency / Branch / Joinなどの構造が問題に適合しているか | Topology, dependency, structural constraints |
| Evaluation | 成功判定、Evidence、Judgmentが分離され、観測可能か | Execution Trace, RunEvaluation, Verifier / Evidence separation |

`Harness` はDATの新しいArchitecture Planeではありません。複数の既存責務を横断して診断するための呼び名です。

## Crosswalk

| Architecture Plane | Prompt | Context | Harness | Loop | Graph | Evaluation |
|---|---:|---:|---:|---:|---:|---:|
| Desired Organization | ✓ | ✓ |  |  | ✓ |  |
| Control Plane |  | ✓ |  | ✓ | ✓ |  |
| Runtime Mapping |  |  | ✓ |  |  |  |
| Observed Execution |  | ✓ | ✓ | ✓ | ✓ | ✓ |
| Evaluation |  |  | ✓ |  |  | ✓ |

この表は所有権を示すものではなく、**一次診断で確認しやすい交点**を示します。

## Diagnostic contract

障害や設計課題を議論するときは、可能な範囲で次を明示します。

1. **Affected Engineering Layer** — どのLayerが主な疑いか
2. **Broken Work Unit** — 何が壊れたか。Role、adapter、handoff、policy、validatorなど、最小の作業単位で記述する
3. **Expected Invariant** — 本来守られるべき性質
4. **Observed Evidence** — 実際に観測された事実
5. **Verification Method** — 修正後にInvariantをどう検証するか

例:

```text
Affected Engineering Layer: Harness
Broken Work Unit: verifier capability binding
Expected Invariant: verifier has no write capability
Observed Evidence: runtime trace shows a write-capable tool binding
Verification Method: capability manifest validation + runtime trace
```

## Diagnosis order

失敗を見つけたとき、最初からTopologyを複雑化しません。

```text
Observable failure
  ↓
Identify the smallest broken work unit
  ↓
Locate the affected Engineering Layer
  ↓
State the expected invariant
  ↓
Apply the smallest corrective change
  ↓
Verify with deterministic / observable evidence
  ↓
Escalate complexity only if the simpler layer cannot address the failure
```

次のような短絡を避けます。

- Promptの曖昧さをAgent追加で隠す
- Context不足をRetry回数の増加で隠す
- Permission欠陥をRole instructionだけで補う
- Harness欠陥をModel性能の問題と決めつける
- Evaluation不足をReviewerの主観的承認で補う
- 単発Failureだけを根拠にGraphを複雑化する

## Relationship to EXP-001

この診断レンズは既存概念の整理であり、EXP-001のPrompt、Topology、Role、Scenario、Fixture、Schema、validator、Run Matrix、Metric、Decision semanticsを変更しません。

新しいLoop contract、state model、branch/join semantics、recovery edgeなどのMachine-readable contractは、この文書の導入だけを根拠に追加しません。必要性をEvidenceで確認し、active experiment freezeと通常のResearch Proposalプロセスに従って別途検討します。
