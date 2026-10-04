# Gemini CLI adapter

v0.2.1では **Manual Adapter** を標準とします。

- DATの正本: `.dat/`
- Runtime側設定: `GEMINI.md`
- Capability contract: `capabilities.yaml`
- 自動compile/apply: 未実装

導入時は `.dat/runtimes.yaml` の `configPath` でRuntime設定を明示し、DAT validatorでRuntime名とCapability manifestの参照整合を確認します。

DATは既存Runtime設定を自動上書きしません。
