set -euo pipefail
STOP() { echo "STOP: $*"; exit 1; }
has() { local rc=0; grep "$@" || rc=$?; [ "$rc" -le 1 ] || STOP "grep error (rc=$rc)"; return "$rc"; }
CX=/cx/bin/codex
EXPECT_APPROVAL=Never
PROMPT_SHA=d98fdfb3c56ecc5659466d8b4ba607bb94e77c2a7d74360175b9657b6b93bf86
# run <label> <allow-nonzero:0|1> <cmd...>: stdout+stderr -> OUT; STOP on timeout / missing command / empty output (and nonzero rc unless allowed)
run() {
  local label=$1 allow=$2 rc=0; shift 2
  OUT=$(timeout 120 "$@" 2>&1) || rc=$?
  [ "$rc" -ne 124 ] || STOP "$label: timeout"
  [ "$rc" -ne 126 ] && [ "$rc" -ne 127 ] || STOP "$label: command not executable (rc=$rc)"
  [ "$allow" = 1 ] || [ "$rc" -eq 0 ] || STOP "$label: exit $rc"
  [ -n "$OUT" ] || STOP "$label: empty output"
  RC=$rc
}
# env_check <keys>: only key names are inspected; values are never printed
env_check() {
  local keys=$1 hits rc=0
  has -qx PATH <<<"$keys" || STOP "env key listing lacks PATH (listing failed?)"
  hits=$(grep -E 'OPENAI|TOKEN|KEY|AUTH' <<<"$keys") || rc=$?
  [ "$rc" -le 1 ] || STOP "grep error (rc=$rc)"
  [ "$rc" -eq 1 ] && return 0
  [ "$hits" = GPG_KEY ] && [ "${GPG_KEY-}" = 7169605F62C751356D054A26A821E680E5FA6305 ] && return 0
  STOP "auth-like env keys present: $(tr '\n' ' ' <<<"$hits")"
}

run version 0 "$CX" --version
printf '%s\n' "$OUT"
has -qxF 'codex-cli 0.160.0' <<<"$OUT" || STOP "codex version is not 0.160.0"
echo "PASS: codex-cli 0.160.0"

[ -f /tmp/codex-home/auth.json ] && [ -s /tmp/codex-home/auth.json ] || STOP "auth.json is not mounted (missing or empty)"
run login 0 "$CX" login status
printf '%s\n' "$OUT"
has -qxF 'Logged in using ChatGPT' <<<"$OUT" || STOP "login status is not 'Logged in using ChatGPT'"
echo "PASS: logged in using ChatGPT"

run config 0 cat "$CODEX_HOME/config.toml"
printf '%s\n' "$OUT"
has -qxF 'default_permissions = "t1-workspace"' <<<"$OUT" || STOP "config lacks default_permissions = t1-workspace"
has -qxF '"/tmp/codex-home" = "deny"' <<<"$OUT" || STOP "config lacks /tmp/codex-home deny"
if has -Eq '^[[:space:]]*sandbox_mode' <<<"$OUT"; then STOP "config contains sandbox_mode"; fi
echo "PASS: config.toml content"

run doctor 1 "$CX" --strict-config doctor --all --ascii --no-color
printf '%s\n' "$OUT"
echo "doctor-exit=$RC"
has -Eq '\[ok\] config +(config )?loaded' <<<"$OUT" || STOP "doctor: config not [ok] loaded"
has -Eq 'config\.toml parse +ok' <<<"$OUT" || STOP "doctor: config.toml parse not ok"
has -Eq 'model +gpt-6\.1-sol' <<<"$OUT" || STOP "doctor: model is not gpt-6.1-sol"
has -Eq "\[ok\] sandbox .*approval $EXPECT_APPROVAL" <<<"$OUT" || STOP "doctor: sandbox line not [ok] with approval $EXPECT_APPROVAL"
has -Eq '\[ok\] auth +auth is configured' <<<"$OUT" || STOP "doctor: auth not configured"
if has -Eq 'unrecognized configuration setting|is ignored' <<<"$OUT"; then STOP "doctor: startup warning about config keys"; fi
echo "PASS: doctor lines"

run prompt-sha 0 sha256sum /run-input/prompt.md
printf '%s\n' "$OUT"
[ "${OUT%% *}" = "$PROMPT_SHA" ] || STOP "prompt SHA-256 mismatch"
echo "PASS: prompt SHA-256"

run sandbox-ok 0 "$CX" sandbox -P t1-workspace -C /work -- bash -lc 'echo SANDBOX_OK'
printf '%s\n' "$OUT"
has -qxF SANDBOX_OK <<<"$OUT" || STOP "sandbox did not print SANDBOX_OK"
echo "PASS: sandbox starts"

read -r -d '' AUTH_PROBE <<'P' || true
set -euo pipefail
echo SANDBOX_ALIVE
command -v cat >/dev/null || { echo "UNKNOWN: cat missing"; exit 4; }
if err=$(cat /tmp/codex-home/auth.json 2>&1 >/dev/null); then echo "BLOCK: sandbox can read auth file"; exit 3; fi
case $err in *"Permission denied"*|*"No such file or directory"*) echo AUTH_DENIED ;; *) echo "UNKNOWN: unexpected error class"; exit 4 ;; esac
P
run auth-probe 0 "$CX" sandbox -P t1-workspace -C /work -- bash -lc "$AUTH_PROBE"
printf '%s\n' "$OUT"
has -qxF SANDBOX_ALIVE <<<"$OUT" || STOP "auth probe did not run inside sandbox"
has -qxF AUTH_DENIED <<<"$OUT" || STOP "auth probe did not report AUTH_DENIED"
echo "PASS: auth file exists (container side) and is not readable inside sandbox"

keys=$(compgen -e) || STOP "compgen -e failed"
env_check "$keys"
echo "PASS: no auth-like env keys in container shell (GPG_KEY image default allowed)"

read -r -d '' ENV_PROBE <<'P' || true
set -euo pipefail
echo SANDBOX_ALIVE
compgen -e | sed 's/^/KEY /'
echo ENV_LIST_END
P
run env-probe 0 "$CX" sandbox -P t1-workspace -C /work -- bash -lc "$ENV_PROBE"
has -qxF SANDBOX_ALIVE <<<"$OUT" || STOP "env probe did not run inside sandbox"
has -qxF ENV_LIST_END <<<"$OUT" || STOP "env probe listing incomplete"
skeys=$(sed -n 's/^KEY //p' <<<"$OUT")
printf '%s\n' "$skeys"
env_check "$skeys"
echo "PASS: no auth-like env keys inside sandbox (GPG_KEY image default allowed)"

run find-work 0 find /work -maxdepth 3
printf '%s\n' "$OUT"
run ls-run-input 0 ls -la /run-input
printf '%s\n' "$OUT"
run ls-A 0 ls -A /run-input
[ "$OUT" = prompt.md ] || STOP "/run-input contains something other than prompt.md"
echo "PASS: /run-input contains only prompt.md (compare /work listing with Gate 6 fixture set manually)"
echo "PASS: preflight (d) container checks complete"
