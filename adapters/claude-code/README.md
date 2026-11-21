# Claude Code adapter

v0.2.1では **Manual Adapter** を標準とします。

- DATの正本: `.dat/`
- Runtime側設定: `CLAUDE.md`
- Capability contract: `capabilities.yaml`
- 自動compile/apply: 未実装
- ウェーブ観察記録の手順: [RUN_OBSERVATION.md](RUN_OBSERVATION.md)

導入時は `.dat/runtimes.yaml` の `configPath` でRuntime設定を明示し、DAT validatorでRuntime名とCapability manifestの参照整合を確認します。

DATは既存Runtime設定を自動上書きしません。

## Subagent foldingのread-only事前確認（2026-11-15の仕様照合）

[#248の共通実験設計](../../docs/SUBAGENT_FOLDING_DESIGN.md)に対するClaude Code固有の静的確認。管理作業環境では `claude` CLIを確認できず、Operator側の実効設定・Skill/Subagent発火・Traceは **NOT_TESTED**。

- [`capabilities.yaml`](capabilities.yaml) では分離機能を `native` と宣言している。ただしOperator環境での実効Permission・Context隔離を証明するものではない。
- Subagentの `tools` / `disallowedTools` はTool制限を設定する。一方、Skillの `allowed-tools` は呼び出しturnに対するToolの許可を事前付与するもので、使用可能Toolの上限を強制する代替ではない。F0の権限をF1に単純unionしない。
- mainのmodeが `bypassPermissions`、`acceptEdits`、`auto` の場合、Subagentの `permissionMode` 指定もmainの実効modeに従うことがある。実効mode・Tool allow/deny・拒否結果をRuntime上で確認できなければ **P1 HOLD**。
- Skillのモデルによる呼び出しと `/skill-name` 直接起動ではHook経路が異なるため、起動方式を先に固定し、独立Transcript・Tool結果と照合する。

参照（2026-11-15時点で照合した公式仕様）: [Subagents](https://code.claude.com/docs/en/sub-agents)、[Skills](https://code.claude.com/docs/en/skills)、[Hooks](https://code.claude.com/docs/en/hooks)。仕様はRuntime版・実行環境に依存するため、Operator環境で再確認する。

Operator候補環境で**モデルを起動せず**、CLIが使える場合だけ以下の静的コマンドを確認する。未インストールの場合はUNKNOWNとする。

```sh
claude --version
claude --help
```

`claude -p`、モデルへの試験指示、負の権限probe、有料モデル実行はP0対象外。Subagent/Skillの宣言が存在しても実activationの証拠にはならない。
