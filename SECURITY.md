# Security Policy

DAT specifications and tooling can influence how AI agents are selected, permissioned, and evaluated. Security reports should therefore treat configuration, prompts, traces, and runtime permissions as potentially sensitive.

## Supported versions

Security fixes are prioritized for the latest `main` revision and the latest published release. Older snapshots are supported on a best-effort basis.

## Reporting a vulnerability

Do **not** open a public issue containing exploit details, secrets, private source code, confidential prompts, or unsanitized traces.

Start from the repository's GitHub Security page:

https://github.com/s977043/dynamic-agent-topology/security

When **Report a vulnerability** is available there, use GitHub's private vulnerability reporting flow. If private vulnerability reporting is not available, contact the repository maintainer through a private channel associated with their GitHub profile and provide only the minimum information needed to establish contact.

Do not move sensitive details into a public Issue or Pull Request just because a private reporting option is unavailable.

A useful report includes:

- affected DAT version or commit;
- affected file, adapter, workflow, or runtime boundary;
- impact and realistic attack preconditions;
- minimal reproduction or proof of concept;
- suggested mitigation, if known.

Please avoid accessing data that does not belong to you or expanding a proof of concept beyond what is necessary to demonstrate the issue.

## Response and disclosure expectations

The project aims to:

- acknowledge a vulnerability report within **7 calendar days**;
- provide a status update within **14 calendar days** when investigation or remediation is still in progress;
- coordinate public disclosure after a fix or mitigation is available, or on another date agreed with the reporter.

These are response goals rather than a contractual SLA. Severity, exploitability, upstream dependencies, and maintainer availability can affect timing.

Do not publicly disclose unresolved exploit details without coordinating with the maintainer first. The maintainer should likewise avoid unnecessary disclosure of reporter identity or sensitive reproduction material.

## Security boundaries

Do not commit secrets, private source code, raw prompts containing confidential data, or unsanitized execution traces.

Adapters and harness implementations should default to least privilege. Runtime permissions must not be inferred from role names alone. Prompt-level instructions are not an enforcement boundary.

## Experiment commands

`evidenceCommands` are declarative experiment inputs and must be treated as untrusted content. Generic tooling must not execute contributed commands through an unrestricted shell without explicit trust, sandboxing, and least-privilege controls.

The repository CI validates the bundled EXP-001 fixtures with a fixed Python unittest invocation rather than executing `evidenceCommands` directly.

## GitHub Actions

Repository workflows should:

- use the minimum required `GITHUB_TOKEN` permissions;
- pin reusable actions to immutable commit SHAs;
- avoid exposing credentials to untrusted pull-request code;
- keep dependency updates automated and reviewable.

Security fixes that do not change frozen EXP-001 semantics are allowed during the active feature freeze.
