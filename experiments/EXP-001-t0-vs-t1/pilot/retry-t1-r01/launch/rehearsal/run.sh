#!/bin/bash
# EXP-001 launch-kit rehearsal: practice task only (not EXP-001). Real auth :ro bind, one codex exec.
set -uo pipefail
N="${1:?rehearsal number}"
# Required environment (no absolute paths are hard-coded):
#   WORK_ROOT  host directory outside Git for rehearsal outputs (r<N>/ is created under it)
#   REPO       local clone of dynamic-agent-topology (origin/main is used for the seccomp profile)
#   CODEX_DIR  host directory of the Codex 0.160.0 linux-arm64 musl vendor tree (mounted at /cx:ro)
: "${WORK_ROOT:?}" "${REPO:?}" "${CODEX_DIR:?}"
KIT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
R="$WORK_ROOT/r$N"
CNAME="exp001-rehearsal-$N"
TIMEOUT_S=900

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$R/status.log"; }
stop() { log "STOP: $*"; docker stop "$CNAME" >/dev/null 2>&1 && log "container stopped" || log "container stop: not running"; summary; exit 1; }
summary() {
  {
    echo "=== rehearsal $N summary ==="
    echo "codex-exit: $(cat "$R/sink/codex-exit" 2>/dev/null || echo missing)"
    echo "started: $(cat "$R/sink/started-at" 2>/dev/null || echo missing)  finished: $(cat "$R/sink/finished-at" 2>/dev/null || echo missing)"
    echo "tests-after: $(cat "$R/tests-after.txt" 2>/dev/null | tail -1 || echo missing)"
    echo "evidence files: $(tar -tf "$R/sink/evidence.tar" 2>/dev/null | wc -l | tr -d ' ')"
    echo "secret-pattern hits: $(cat "$R/secret-hits" 2>/dev/null || echo not-scanned)"
    echo "container left: $(docker ps -q --filter name="^$CNAME$" | wc -l | tr -d ' ')"
  } | tee -a "$R/status.log"
}

[ -e "$R" ] && { echo "STOP: $R exists"; exit 1; }
mkdir -m 700 -p "$R/ws" "$R/run-input" "$R/sink"
log "rehearsal $N start"
cp -R "$KIT/fixture/." "$R/ws/" || stop "copy fixture"
cp "$KIT/prompt.md" "$R/run-input/prompt.md" || stop "copy prompt"
git -C "$REPO" show origin/main:experiments/EXP-001-t0-vs-t1/pilot/retry-t1-r01/codex-bwrap-seccomp.json > "$R/seccomp.json" || stop "seccomp extract"
[ "$(shasum -a 256 < "$R/seccomp.json" | cut -c1-64)" = 085e468fa8e70d8c839a9abab4d74a1ab2abad74a8c26f15234ba62a8ac2e1e8 ] || stop "seccomp sha"
(cd "$R/ws" && python3 -m unittest discover -s tests > "$R/tests-before.txt" 2>&1); log "tests-before rc=$? ($(tail -1 "$R/tests-before.txt"))"

docker run --rm -dit --name "$CNAME" --platform linux/arm64 \
  --security-opt seccomp="$R/seccomp.json" --security-opt no-new-privileges \
  --cap-drop ALL --user "$(id -u):$(id -g)" \
  --read-only --tmpfs /tmp \
  --tmpfs /tmp/codex-home:uid="$(id -u)",gid="$(id -g)",mode=700 \
  -e HOME=/tmp/home -e CODEX_HOME=/tmp/codex-home \
  -v "$HOME/.codex/auth.json":/tmp/codex-home/auth.json:ro \
  -v "$CODEX_DIR":/cx:ro \
  -v "$R/run-input/prompt.md":/run-input/prompt.md:ro \
  -v "$R/ws":/work -w /work \
  python@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258 \
  bash -l >/dev/null || stop "docker run"
log "container up"

docker exec -i "$CNAME" bash -l > "$R/setup.log" 2>&1 <<'SETUP' || stop "setup (see setup.log)"
set -euo pipefail
mkdir -p "$HOME" "$CODEX_HOME"
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

[projects."/work"]
trust_level = "trusted"
EOF
/cx/bin/codex --version
ls_out=$(/cx/bin/codex login status 2>&1) || { echo "login status failed"; exit 1; }
grep -q '^Logged in using ChatGPT' <<<"$ls_out" || { echo "not logged in"; exit 1; }
echo "login: ok"
out=$(/cx/bin/codex sandbox -P t1-workspace -C /work -- bash -lc 'cat /tmp/codex-home/auth.json >/dev/null 2>&1 && echo AUTH_READABLE || echo AUTH_DENIED') || { echo "sandbox failed"; exit 1; }
echo "$out"
[ "$out" = AUTH_DENIED ] || exit 1
SETUP
log "setup ok: $(tr '\n' ' ' < "$R/setup.log")"

log "codex exec start (timeout ${TIMEOUT_S}s)"
timeout "$TIMEOUT_S" docker exec -i "$CNAME" bash -l > "$R/codex-stdout.log" 2>&1 <<'RUN'
date '+%Y-%m-%dT%H:%M:%S%z' > /tmp/started-at
/cx/bin/codex exec --skip-git-repo-check -C /work - < /run-input/prompt.md
rc=$?
echo $rc > /tmp/codex-exit
date '+%Y-%m-%dT%H:%M:%S%z' > /tmp/finished-at
exit $rc
RUN
HOST_RC=$?
log "docker exec returned rc=$HOST_RC"
[ "$HOST_RC" = 124 ] && log "TIMEOUT"

docker exec "$CNAME" tar -C /tmp -cf - started-at finished-at codex-exit codex-home/sessions > "$R/sink/evidence.tar" 2>"$R/collect.err"
COLLECT_RC=$?
log "collect rc=$COLLECT_RC ($(tar -tf "$R/sink/evidence.tar" 2>/dev/null | wc -l | tr -d ' ') entries)"
AUTH_IN_EVIDENCE=0
tar -tf "$R/sink/evidence.tar" | grep -q 'auth.json' && { AUTH_IN_EVIDENCE=1; log "FAIL: auth.json in evidence"; }
tar -xf "$R/sink/evidence.tar" -C "$R/sink" started-at finished-at codex-exit 2>/dev/null
chmod 600 "$R/sink/evidence.tar"
SCAN_OK=1
mkdir -p "$R/scan" && tar -xf "$R/sink/evidence.tar" -C "$R/scan" || { log "FAIL: evidence extraction for secret scan"; SCAN_OK=0; }
grep -rlE 'eyJ[A-Za-z0-9_-]{20}|sk-[A-Za-z0-9]{16}|"(access|refresh|id)_token"|Bearer [A-Za-z0-9]' "$R/scan" "$R/codex-stdout.log" > "$R/secret-files" 2>"$R/scan.err"
case $? in
  0) wc -l < "$R/secret-files" | tr -d ' ' > "$R/secret-hits" ;;
  1) echo 0 > "$R/secret-hits" ;;
  *) log "FAIL: secret scan error"; SCAN_OK=0; echo error > "$R/secret-hits" ;;
esac
rm -f "$R/secret-files"
rm -rf "$R/scan"

docker stop "$CNAME" >/dev/null 2>&1 && log "container stopped" || log "WARN: container stop failed"
(cd "$R/ws" && python3 -m unittest discover -s tests > "$R/tests-after.txt" 2>&1); log "tests-after rc=$?"
summary

FAIL=0
[ "$HOST_RC" = 0 ] || { log "FAIL: codex exec rc=$HOST_RC"; FAIL=1; }
[ "$COLLECT_RC" = 0 ] || { log "FAIL: evidence collection rc=$COLLECT_RC"; FAIL=1; }
[ "$AUTH_IN_EVIDENCE" = 0 ] || FAIL=1
[ "$SCAN_OK" = 1 ] || FAIL=1
[ "$(cat "$R/secret-hits" 2>/dev/null)" = 0 ] || { log "FAIL: secret pattern scan not clean"; FAIL=1; }
[ "$(docker ps -q --filter name="^$CNAME$" | wc -l | tr -d ' ')" = 0 ] || { log "FAIL: container left running"; FAIL=1; }
[ "$FAIL" = 0 ] && log "PASS: rehearsal $N" || log "STOP: rehearsal $N failed a mandatory gate"
exit "$FAIL"
