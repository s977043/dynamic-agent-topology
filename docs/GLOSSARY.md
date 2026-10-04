# Glossary

- **Agent**: An executable AI participant operating within a runtime.
- **Role**: A responsibility contract independent of model/runtime.
- **Topology**: Declared structure of roles/nodes, relationships, dependencies, and constraints.
- **Routing Policy**: Rules selecting a topology.
- **Escalation / De-escalation**: Moving to more / less coordinated structures.
- **Runtime**: Execution environment such as Claude Code, Codex, Gemini CLI, or Antigravity.
- **Adapter**: Mapping from DAT abstractions to runtime-native constructs.
- **Evidence**: Observable information used to judge execution.
- **Verifier**: Role that gathers/interprets evidence; not ground truth.
- **Adherence**: How closely observed execution follows the declared topology.
- **Ablation**: Removing a role/edge/mechanism to measure marginal value.
- **Project Binding**: Project-specific DAT configuration under `.dat/`.

- **Runtime Binding**: Project-specific mapping between DAT runtime names and existing runtime configuration files.
- **DAT Lock**: Version/source binding used to make an adopting project's DAT contract explicit and reproducible.
- **Manual Adapter**: A runtime integration mode where DAT validates the binding but does not generate or overwrite runtime-native configuration.
