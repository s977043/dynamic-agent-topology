#!/bin/bash
# Proves that the kit differs from the T1 r01 kit only in Run-specific values (no Docker, no Codex, no model).
# Rendering the templates with the T1 r01 values (train-normalize-name, prompt d98fdfb3...) must reproduce the
# T1 r01 doc-extracted scripts byte for byte; the unchanged scripts must equal them as-is.
# usage: selftest.sh <python 3.12>
set -euo pipefail
PY=${1:?python 3.12}
KIT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
sha() { shasum -a 256 < "$1" | cut -c1-64; }
fail=0
check() { if [ "$(sha "$1")" = "$2" ]; then echo "OK   $3"; else echo "FAIL $3"; fail=1; fi; }
T1R01_PROMPT=d98fdfb3c56ecc5659466d8b4ba607bb94e77c2a7d74360175b9657b6b93bf86
EXPECT=()
while IFS= read -r l; do EXPECT+=("$l"); done < <("$PY" -I -B "$KIT/host/gates.py" expect --expectations "$KIT/expectations/gate11.tsv" --scenario train-normalize-name)
"$PY" -I -B "$KIT/host/render.py" "$KIT/container/nonmodel-1-5.sh.in" "$T/nonmodel-1-5.sh" "${EXPECT[@]}"
for n in container/preflight-d.sh host/host-mounts.sh host/prompt-copy.sh; do
  "$PY" -I -B "$KIT/host/render.py" "$KIT/$n.in" "$T/$(basename "$n")" "PROMPT_SHA256=$T1R01_PROMPT"
done
# T1 r01 pins: retry-t1-r01/launch/SHA256SUMS (doc-extracted/*) and the (g) block of docs/EXP-001_RETRY_T1_R01_PYTHON_ENV.md
check "$T/nonmodel-1-5.sh" ca2e28b85482fa65a5119eeddab18f0542ea7c8978af88b2e6ac7cd802753159 "nonmodel-1-5.sh rendered for train-normalize-name == T1 r01"
check "$T/preflight-d.sh" edc80a37fe68ce4b18c1b320f427bf640e6a1f4b51e99780f829382fd297219e "preflight-d.sh rendered for T1 r01 prompt == T1 r01"
check "$T/host-mounts.sh" 5f0163464824aa971c66fcfbb6d2bf36ea42c1b97a1e2634a77221e63ff98264 "host-mounts.sh rendered for T1 r01 prompt == T1 r01"
check "$T/prompt-copy.sh" edab57dc5c9bf83d185e2b7d1c234704341182f260d5caab3d72b841fd16cd51 "prompt-copy.sh rendered for T1 r01 prompt == T1 r01"
check "$KIT/container/proc-check.sh" c630213b7c76818d3503421757a2ea150ae25cac6fd2fddc7e68132f96d50473 "proc-check.sh == T1 r01 (unchanged)"
check "$KIT/container/config-never.sh" fde8214f15a057716b2cb4c3189edefb36c5f7fb0c8d7c65e9e229d54e86602a "config-never.sh == T1 r01 (unchanged)"
check "$KIT/host/collect-evidence.sh" 63f27d2ddc2bfb345fe916b2d636da91eb4b35dc2b3a6227a963c4212f012f0f "collect-evidence.sh == T1 r01 (unchanged)"
check "$KIT/container/g.sh" 75354c63ba8c28af78a167d13e527dfac382c18feaa7592bae5b0b14491e97d9 "g.sh == T1 r01 (g) block (unchanged)"
# Every scenario renders, and a value that could change shell syntax is rejected.
for s in train-normalize-name test-clamp-boundaries regression-safe-divide practice-leap; do
  EXPECT=()
  while IFS= read -r l; do EXPECT+=("$l"); done < <("$PY" -I -B "$KIT/host/gates.py" expect --expectations "$KIT/expectations/gate11.tsv" --scenario "$s")
  if "$PY" -I -B "$KIT/host/render.py" "$KIT/container/nonmodel-1-5.sh.in" "$T/nonmodel-$s.sh" "${EXPECT[@]}" && bash -n "$T/nonmodel-$s.sh"; then echo "OK   render $s"; else echo "FAIL render $s"; fail=1; fi
done
if "$PY" -I -B "$KIT/host/render.py" "$KIT/host/prompt-copy.sh.in" "$T/bad.sh" 'PROMPT_SHA256=$(id)' 2>/dev/null; then echo "FAIL unsafe value accepted"; fail=1; else echo "OK   unsafe value rejected"; fi
# Negative tests of the record formats, the attempt registry and run.sh argument gates (no network, Docker or gh).
G() { "$PY" -I -B "$KIT/host/gates.py" "$@"; }
expect() { # expect <PASS|STOP> <name> <command...>
  local want=$1 name=$2 rc=0; shift 2
  "$@" > "$T/out" 2>&1 || rc=$?
  if { [ "$want" = PASS ] && [ "$rc" = 0 ]; } || { [ "$want" = STOP ] && [ "$rc" != 0 ] && grep -q 'STOP' "$T/out"; }; then
    echo "OK   $want: $name -> $(tail -1 "$T/out" | cut -c1-160)"
  else
    echo "FAIL expected $want: $name (rc=$rc: $(tail -1 "$T/out"))"; fail=1
  fi
}
R=$T/registry
RID=EXP-001-train-normalize-name-r02-T1
REPO_TOP=$(git -C "$KIT" rev-parse --show-toplevel)
mkdir -m 700 "$R" "$T/wr" "$T/wr2" "$T/home" "$T/shim"
printf 'dummy\n' > "$T/auth.json"
# attempt registry: re-prepare, missing / unreadable registry, HOME that differs from the user database
expect PASS "first attempt is reserved" G reserve-attempt --registry "$R" --run-id "$RID" --expect-existing 0
expect STOP "re-prepare of a runId with an existing attempt" G reserve-attempt --registry "$R" --run-id "$RID" --expect-existing 0
expect PASS "attempt 2 with the existing attempt acknowledged" G reserve-attempt --registry "$R" --run-id "$RID" --expect-existing 1
expect STOP "attempt registry not found" G attempt-count --registry "$T/no-registry" --run-id "$RID"
mkdir -m 755 "$T/open-registry"
expect STOP "attempt registry with a mode other than 700" G attempt-count --registry "$T/open-registry" --run-id "$RID"
expect STOP "HOME differs from the user database home" env HOME="$T/home" "$PY" -I -B "$KIT/host/gates.py" registry-path
RUNARGS=(--run-id "$RID" --workspace-id exp001-selftest-ws --fixture fixtures/exp-001/train/normalize-name --work-root "$T/wr"
  --repo "$REPO_TOP" --codex-dir "$T" --python "$PY" --auth-file "$T/auth.json" --prior-accept-comment 1 --env-judgment-comment 2)
expect STOP "run.sh real mode with a changed HOME" env HOME="$T/home" bash "$KIT/run.sh" "${RUNARGS[@]}"
expect STOP "run.sh real mode with --practice-model" bash "$KIT/run.sh" "${RUNARGS[@]}" --practice-model
[ -z "$(ls -A "$T/wr")" ] && echo "OK   run.sh stopped before creating any run directory" || { echo "FAIL run.sh created files"; fail=1; }
# a failing command with empty output must not pass a check (docker ps fails before the container-exists check)
printf '#!/bin/sh\nexit 1\n' > "$T/shim/docker"
chmod 700 "$T/shim/docker"
expect STOP "docker ps fails with empty output" env PATH="$T/shim:$PATH" bash "$KIT/run.sh" --mode practice --run-id PRACTICE-leap-r01 \
  --workspace-id practice-selftest-ws --fixture experiments/EXP-001-t0-vs-t1/pilot/run-kit-g/rehearsal/fixture --work-root "$T/wr2" \
  --repo "$REPO_TOP" --codex-dir "$T" --python "$PY" --auth-file "$T/auth.json"
grep -q 'docker ps failed' "$T/out" && echo "OK   STOP reason is the failed docker ps" || { echo "FAIL STOP reason: $(tail -2 "$T/out" | head -1)"; fail=1; }
# record formats (Reviewer line with runtime / model / session is required in all three)
pipe() { local body=$1; shift; printf '%s\n' "$body" | G "$@"; }
EJ=(env-judgment --repo "$REPO_TOP" --main-ref HEAD --kitrel experiments/EXP-001-t0-vs-t1/pilot/run-kit-g --kit-dir "$KIT")
L='https://github.com/s977043/dynamic-agent-topology/issues/15#issuecomment-1'
L2='https://github.com/s977043/dynamic-agent-topology/pull/135'
L3='https://github.com/s977043/dynamic-agent-topology/issues/15#issuecomment-3'
EV="evidence: https://github.com/s977043/dynamic-agent-topology/pull/200"
RV='Reviewer: 独立 Reviewer（runtime: codex 0.160.1、model: gpt-6-luna、session: `01a129b7-f13d-74c1-977d-9f6477bdf150`）'
HEAD_SHA=$(git -C "$REPO_TOP" rev-parse HEAD)
env_body() { printf '%s\nEXP-001 r02+ environment disposition: ACCEPT\nkit: PR #135 merge %s\ncondition-1: %s\ncondition-2: %s\ncondition-3: %s' "$1" "$2" "$L" "${3:-$L2}" "$L3"; }
expect STOP "CONDITIONAL ACCEPT environment Judgment" pipe "$(printf '%s\nEXP-001 r02+ environment disposition: CONDITIONAL ACCEPT' "$RV")" "${EJ[@]}"
expect STOP "ACCEPT line plus a CONDITIONAL line" pipe "$(env_body "$RV" "$HEAD_SHA")
EXP-001 r02+ environment disposition: CONDITIONAL ACCEPT" "${EJ[@]}"
expect STOP "ACCEPT without condition evidence lines" pipe "$(printf '%s\nEXP-001 r02+ environment disposition: ACCEPT\nkit: PR #135 merge %s' "$RV" "$HEAD_SHA")" "${EJ[@]}"
expect STOP "ACCEPT for a kit merge that is not on main" pipe "$(env_body "$RV" "$(printf '%040d' 0)")" "${EJ[@]}"
expect STOP "environment Judgment with duplicated condition links" pipe "$(env_body "$RV" "$HEAD_SHA" "$L")" "${EJ[@]}"
expect STOP "environment Judgment without a Reviewer line" pipe "$(env_body '' "$HEAD_SHA")" "${EJ[@]}"
expect STOP "environment Judgment whose Reviewer line lacks the session" pipe "$(env_body 'Reviewer: runtime: codex, model: gpt-6-luna' "$HEAD_SHA")" "${EJ[@]}"
if git -C "$REPO_TOP" show "HEAD:experiments/EXP-001-t0-vs-t1/pilot/run-kit-g/SHA256SUMS" 2>/dev/null | cmp -s - "$KIT/SHA256SUMS"; then
  expect PASS "unconditional ACCEPT with Reviewer record for this kit (HEAD as main)" pipe "$(env_body "$RV" "$HEAD_SHA")" "${EJ[@]}"
else
  echo "SKIP positive environment Judgment case (kit not committed at HEAD)"
fi
expect STOP "Run acceptance without a runId line" pipe "$(printf '%s\nEXP-001 Run acceptance: ACCEPT\n%s' "$RV" "$EV")" run-acceptance --run-id "$RID"
expect STOP "Run acceptance for another runId" pipe "$(printf '%s\nEXP-001 Run acceptance: ACCEPT\nrunId: EXP-001-train-normalize-name-r02-T0\n%s' "$RV" "$EV")" run-acceptance --run-id "$RID"
expect STOP "Run acceptance without a Reviewer line" pipe "$(printf 'EXP-001 Run acceptance: ACCEPT\nrunId: %s\n%s' "$RID" "$EV")" run-acceptance --run-id "$RID"
expect STOP "Run acceptance without an evidence link" pipe "$(printf '%s\nEXP-001 Run acceptance: ACCEPT\nrunId: %s' "$RV" "$RID")" run-acceptance --run-id "$RID"
expect STOP "Run acceptance with a malformed evidence link" pipe "$(printf '%s\nEXP-001 Run acceptance: ACCEPT\nrunId: %s\nevidence: https://example.com/pull/1' "$RV" "$RID")" run-acceptance --run-id "$RID"
expect PASS "Run acceptance in record format" pipe "$(printf '%s\nEXP-001 Run acceptance: ACCEPT\nrunId: %s\n%s' "$RV" "$RID" "$EV")" run-acceptance --run-id "$RID"
SD=$(printf 'EXP-001 slot disposition: NEW-ATTEMPT\nrunId: %s\nattempt: 2' "$RID")
RS='reason: preflight STOP before (g) caused by an infrastructure fault; model never started'
expect STOP "slot disposition for a different attempt" pipe "$(printf '%s\n%s\n%s\n%s' "$RV" "$SD" "$RS" "$EV")" slot-disposition --run-id "$RID" --attempt 3
expect STOP "slot disposition without a Reviewer line" pipe "$(printf '%s\n%s\n%s' "$SD" "$RS" "$EV")" slot-disposition --run-id "$RID" --attempt 2
expect STOP "slot disposition without a reason line" pipe "$(printf '%s\n%s\n%s' "$RV" "$SD" "$EV")" slot-disposition --run-id "$RID" --attempt 2
expect STOP "slot disposition without an evidence link" pipe "$(printf '%s\n%s\n%s' "$RV" "$SD" "$RS")" slot-disposition --run-id "$RID" --attempt 2
expect PASS "slot disposition in record format" pipe "$(printf '%s\n%s\n%s\n%s' "$RV" "$SD" "$RS" "$EV")" slot-disposition --run-id "$RID" --attempt 2
[ "$fail" = 0 ] && echo "PASS: selftest" || { echo "STOP: selftest failed"; exit 1; }
