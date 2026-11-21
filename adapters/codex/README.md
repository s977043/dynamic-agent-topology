# Codex adapter

v0.2.1では **Manual Adapter** を標準とします。

- DATの正本: `.dat/`
- Runtime側設定: `AGENTS.md`
- Capability contract: `capabilities.yaml`
- 自動compile/apply: 未実装
- Codex Cloudでの検証範囲・結果: [CLOUD_VERIFICATION.md](CLOUD_VERIFICATION.md)
- ウェーブ観察記録の手順: [RUN_OBSERVATION.md](RUN_OBSERVATION.md)

導入時は `.dat/runtimes.yaml` の `configPath` でRuntime設定を明示し、DAT validatorでRuntime名とCapability manifestの参照整合を確認します。

DATは既存Runtime設定を自動上書きしません。

## Subagent foldingのread-only事前確認（2026-11-15の履歴）

[#248の共通実験設計](../../docs/SUBAGENT_FOLDING_DESIGN.md)に対するCodex固有の静的確認。管理作業環境で観測した事実であり、OperatorのMac・本実験の実効設定ではない。実モデル起動・負の権限probe・真正なTrace取得は **NOT_TESTED**。

| 項目 | 2026-11-15時点の静的確認 | 未解決の境界 |
| --- | --- | --- |
| CLI | `codex-cli 0.167.0-alpha.4`、Python 3.12.14 | Operator環境の版・Model/Effortは未固定 |
| F0起動候補 | `codex features list` は `multi_agent: stable true` を表示 | 専門Subagentの登録・起動・Context分離はNOT_TESTED |
| F1 Skill候補 | DAT配布の `dat-select` / `dat-observe` は存在 | 配送ETA用のF0専門RoleとF1 domain Skillの対は未整備 |
| 設定 | `.codex/config.toml` はapproval/sandboxとPython環境を設定 | F0/F1のTool・Permission対応、Operator側の実効設定は未確認 |
| Trace候補 | `codex exec --help` にJSONL出力オプション `--json` がある | activation・Tool入出力・拒否・再試行・usage・欠測の独立取得は未検証 |
| Capability | [`capabilities.yaml`](capabilities.yaml) のContext/Tool/Workspace分離は `unknown` | 宣言やfeature表示を実効権限制約とみなさない |
| DAT変換 | `ExecutionTrace`/`RunEvaluation`契約は別途存在 | 生JSONLからoracle用イベントへの真正性・完全性を保つ変換は未実装 |

Operator候補環境で**モデルを起動せず**、以下の静的コマンドだけ確認する。未対応・未インストールはUNKNOWNとして記録する。

```sh
codex --version
codex features list
codex exec --help
```

`codex exec` や `codex exec --json` の実行、モデル起動、Secretを用いた試験、未承認の追加課金はP0対象外。機能が宣言されていてもF0/F1実体・強制権限・独立Traceが確認できなければ **P1 HOLD**。
