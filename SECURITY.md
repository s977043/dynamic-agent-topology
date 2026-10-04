# Security

Do not commit secrets, private source code, raw prompts containing confidential data, or unsanitized execution traces.

Adapters and harness implementations should default to least privilege. Runtime permissions must not be inferred from role names alone.

Report sensitive security issues privately to the repository maintainer rather than opening a public exploit report.

## Experiment commands

`evidenceCommands` are declarative experiment inputs and must be treated as untrusted content. Generic tooling must not execute contributed commands through an unrestricted shell without explicit trust, sandboxing, and least-privilege controls.

The repository CI validates the bundled EXP-001 fixtures with a fixed Python unittest invocation rather than executing `evidenceCommands` directly.
