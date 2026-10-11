cat > "$CODEX_HOME/config.toml" <<'EOF'
model = "gpt-6.1-sol"
model_reasoning_effort = "high"
approval_policy = "never"
default_permissions = "t1-workspace"

[permissions.t1-workspace]
description = "workspace-write equivalent; CODEX_HOME (auth.json) hidden from sandboxed commands"
extends = ":workspace"

[permissions.t1-workspace.filesystem]
"/tmp/codex-home" = "deny"
EOF
