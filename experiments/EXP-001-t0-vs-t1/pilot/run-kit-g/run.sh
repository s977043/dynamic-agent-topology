#!/bin/bash
# EXP-001 r02+ candidate G run kit: one matrix Run (or one practice task) per invocation.
# Every Run repeats the full preflight (Gates 1-13, (a)-(f), configuration check). Any failure, unknown result
# or missing evidence is STOP. Only Run-specific values are parameters; the environment is pinned in environment.conf.
# Never prints secret values: auth.json is only bind-mounted :ro; codex output goes to a file and is scanned (counts only).
# --dry-run stops right before (g) (the model is never started).
set -Eeuo pipefail

KIT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
KITREL=experiments/EXP-001-t0-vs-t1/pilot/run-kit-g
PILOT_REL=experiments/EXP-001-t0-vs-t1/pilot
ARTIFACT_ROOT=experiments/EXP-001-t0-vs-t1/runs/pilot-codex
. "$KIT_DIR/environment.conf"
GH_REPO=s977043/dynamic-agent-topology
JUDGMENT_ISSUE=15
JUDGMENT_AUTHOR=s977043
# Attempt registry (real mode): <home from the OS user database>/.exp001-run-kit-g/attempts, resolved by gates.py
# registry-path. It does not follow $HOME; a $HOME that differs from the user database, or a missing/unreadable
# registry, is STOP. One reserved attempt per matrix runId (OPERATOR.md 2).
ATTEMPT_REGISTRY=
TIMEOUT_S=1800
export PYTHONDONTWRITEBYTECODE=1

usage() {
  cat <<'U'
usage: run.sh --run-id ID --workspace-id ID --fixture REL --work-root DIR --repo DIR --codex-dir DIR --python PY
              [--mode real|practice] [--dry-run] [--auth-file FILE]
              [--prior-accept-comment ID --env-judgment-comment ID]   (required in real mode)
              [--slot-disposition-comment ID]   (real mode, only when the runId already has a recorded attempt)
              [--practice-model]                (practice mode: start the model; without it practice is always a dry-run)
U
  exit 2
}
MODE=real DRY_RUN=0 RUN_ID= WSID= FIXTURE= WORK_ROOT= REPO= CODEX_DIR= PY= PRIOR_ACCEPT= ENV_JUDGMENT= SLOT_DISP= PRACTICE_MODEL=0
AUTH_SRC=$HOME/.codex/auth.json
while [ $# -gt 0 ]; do
  case $1 in
    --mode) MODE=$2; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --run-id) RUN_ID=$2; shift 2 ;;
    --workspace-id) WSID=$2; shift 2 ;;
    --fixture) FIXTURE=$2; shift 2 ;;
    --work-root) WORK_ROOT=$2; shift 2 ;;
    --repo) REPO=$2; shift 2 ;;
    --codex-dir) CODEX_DIR=$2; shift 2 ;;
    --python) PY=$2; shift 2 ;;
    --auth-file) AUTH_SRC=$2; shift 2 ;;
    --prior-accept-comment) PRIOR_ACCEPT=$2; shift 2 ;;
    --env-judgment-comment) ENV_JUDGMENT=$2; shift 2 ;;
    --slot-disposition-comment) SLOT_DISP=$2; shift 2 ;;
    --practice-model) PRACTICE_MODEL=1; shift ;;
    *) usage ;;
  esac
done
die() { echo "STOP: $*"; exit 1; }
[ -n "$RUN_ID" ] && [ -n "$WSID" ] && [ -n "$FIXTURE" ] && [ -n "$WORK_ROOT" ] && [ -n "$REPO" ] && [ -n "$CODEX_DIR" ] && [ -n "$PY" ] || usage
case $MODE in
  real)
    [[ $RUN_ID =~ ^EXP-001-[a-z]+-[a-z-]+-r0[1-3]-T[01]$ ]] || die "real mode needs an EXP-001 matrix runId"
    [[ $PRIOR_ACCEPT =~ ^[0-9]+$ ]] && [[ $ENV_JUDGMENT =~ ^[0-9]+$ ]] || die "real mode needs --prior-accept-comment and --env-judgment-comment"
    [ -z "$SLOT_DISP" ] || [[ $SLOT_DISP =~ ^[0-9]+$ ]] || die "--slot-disposition-comment must be a comment id"
    [ "$PRACTICE_MODEL" = 0 ] || die "--practice-model is for practice mode only"
    ATTEMPT_REGISTRY=$("$PY" -I -B "$KIT_DIR/host/gates.py" registry-path) || die "attempt registry: $ATTEMPT_REGISTRY"
    ATTEMPTS=$("$PY" -I -B "$KIT_DIR/host/gates.py" attempt-count --registry "$ATTEMPT_REGISTRY" --run-id "$RUN_ID") || die "attempt registry: $ATTEMPTS"
    if [ "$ATTEMPTS" != 0 ] && [ -z "$SLOT_DISP" ]; then
      die "$RUN_ID already has $ATTEMPTS recorded attempt(s) in $ATTEMPT_REGISTRY; re-prepare/re-run needs a reviewed slot disposition for attempt $((ATTEMPTS + 1)) (--slot-disposition-comment)"
    fi
    [ "$ATTEMPTS" != 0 ] || [ -z "$SLOT_DISP" ] || die "--slot-disposition-comment given but $RUN_ID has no recorded attempt" ;;
  practice)
    [[ $RUN_ID =~ ^PRACTICE-[A-Za-z0-9-]+$ ]] || die "practice mode needs a PRACTICE- runId"
    [ "$FIXTURE" = "$KITREL/rehearsal/fixture" ] || die "practice mode uses only $KITREL/rehearsal/fixture"
    [ -z "$SLOT_DISP" ] || die "--slot-disposition-comment is for real mode only"
    # Practice is a dry-run unless the model start is explicitly requested (organizer decision).
    [ "$PRACTICE_MODEL" = 1 ] || DRY_RUN=1 ;;
  *) usage ;;
esac
REPO_TOP=$(git -C "$REPO" rev-parse --show-toplevel) || die "--repo is not a git checkout"
[ -d "$WORK_ROOT" ] || die "--work-root must exist"
WR=$(realpath "$WORK_ROOT")
case "$WR/" in "$(realpath "$REPO_TOP")"/*) die "--work-root must be outside the repository" ;; esac
STAMP=$(date -u '+%Y%m%dT%H%M%SZ')
LOCK=$WR/locks/$RUN_ID.lock      # existence = (g) may already have started for this runId
RD=$WR/runs/$RUN_ID/$STAMP        # everything for this attempt (outside Git)
WT=$RD/checkout                   # clean isolated checkout (detached origin/main)
WS=$RD/ws                         # fresh external workspace (must not exist)
RUN_INPUT=$RD/run-input           # PROMPT copy outside runs/
SINK=$RD/sink                     # evidence sink (700)
LOGD=$RD/logs
GEN=$RD/kit                       # rendered scripts for this Run
CNAME=exp001-runkit-$(tr 'A-Z' 'a-z' <<<"$RUN_ID")
[ ! -e "$LOCK" ] || die "lock $LOCK exists: the model may already have started for $RUN_ID. Do not run again."
mkdir -m 700 -p "$WR/runs/$RUN_ID"
mkdir -m 700 "$RD" || die "$RD exists"
mkdir -m 700 "$LOGD" "$GEN"

# ---------------------------------------------------------------- helpers
PHASE=init
STARTED_MODEL=0
CONTAINER_UP=0
CONTAINER_STUCK=0
LEFT=unchecked
STATUS_LOG=$RD/status.log
log() { printf '%s [%s] %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$PHASE" "$*" | tee -a "$STATUS_LOG"; }
phase() { PHASE=$1; log "BEGIN"; }
container_gone() { # 0 = `docker ps -a` shows no $CNAME (polled; --rm removal is async)
  local i n
  for i in 1 2 3 4 5 6 7 8 9 10; do
    n=$(docker ps -aq --filter "name=^${CNAME}\$" 2>/dev/null) || { LEFT=unknown; sleep 1; continue; }
    LEFT=$(grep -c . <<<"$n" || true)
    [ "$LEFT" = 0 ] && return 0
    sleep 1
  done
  return 1
}
stop_container() { # 0 = confirmed gone, 1 = auth-bound container may remain (CONTAINER-NOT-STOPPED)
  [ "$CONTAINER_UP" = 1 ] || return "$CONTAINER_STUCK"
  CONTAINER_UP=0
  if docker stop "$CNAME" >/dev/null 2>&1; then log "docker stop ok"; else log "WARN: docker stop failed"; fi
  if container_gone; then log "container gone (docker ps -a: 0)"; return 0; fi
  log "container still present after stop (docker ps -a: $LEFT); docker kill"
  docker kill "$CNAME" >/dev/null 2>&1 || log "WARN: docker kill failed"
  if container_gone; then log "container gone after kill (docker ps -a: 0)"; return 0; fi
  CONTAINER_STUCK=1
  log "CONTAINER-NOT-STOPPED: auth を bind したコンテナが残存 (docker ps -a: $LEFT)。Operator は直ちに \`docker rm -f $CNAME\` を実行"
  return 1
}
# STOP <SAFETY|SECRET|PROTOCOL|UNRECOVERABLE> <reason>: the category only classifies; every check is still executed in order.
STOP() {
  local cat=$1 u; shift
  log "STOP [$cat]: $*"
  if [ "$STARTED_MODEL" = 0 ]; then u="model NOT started"; else u="INFRASTRUCTURE ABORT (model started; Run slot consumed; do not re-run)"; fi
  log "$u"
  if ! stop_container; then log "RESULT: CONTAINER-NOT-STOPPED (underlying: STOP; $u). Run \`docker rm -f $CNAME\` now."; fi
  exit 1
}
ENV_MISMATCH() { STOP PROTOCOL "ENV-MISMATCH: $* (environment differs from the reviewed disposition; a new environment Judgment is required)"; }
on_err() { STOP PROTOCOL "check command failed rc=$1 at line $2 (result unknown)"; }
trap 'on_err $? $LINENO' ERR
trap 'stop_container || exit 1' EXIT
sha() { shasum -a 256 < "$1" | cut -c1-64; }
need() { grep -qxF -- "$1" "$2" || STOP PROTOCOL "missing expected line in $(basename "$2"): $1"; }
inexec() { docker exec -i "$CNAME" bash -l < "$1"; }
gates() { "$PY" -I -B "$KIT_DIR/host/gates.py" "$@"; }
render() { "$PY" -I -B "$KIT_DIR/host/render.py" "$@"; }
hashes() { # file set + SHA-256; any failure (cd, find, shasum) makes the function fail
  (cd "$1" || exit 1; files=$(find . -type f) || exit 1; LC_ALL=C sort <<<"$files" | while IFS= read -r f; do
    h=$(shasum -a 256 < "$f" | cut -c1-64) || exit 1; [ ${#h} = 64 ] || exit 1; printf '%s  %s\n' "$h" "$f"; done)
}
check_comment() { # check_comment <id> <issue|any> <gates record-format subcommand> [args...]: body is checked, never logged
  local id=$1 issue=$2 meta; shift 2
  meta=$(gh api "repos/$GH_REPO/issues/comments/$id" --jq '.user.login + " " + (.issue_url|split("/")|last)') || STOP PROTOCOL "cannot fetch comment $id"
  [ "${meta%% *}" = "$JUDGMENT_AUTHOR" ] || STOP PROTOCOL "comment $id is not by $JUDGMENT_AUTHOR"
  [ "$issue" = any ] || [ "${meta#* }" = "$issue" ] || STOP PROTOCOL "comment $id is not on #$issue"
  gh api "repos/$GH_REPO/issues/comments/$id" --jq .body | gates "$@" >> "$LOGD/judgments.log" || STOP PROTOCOL "comment $id does not satisfy the $1 record format ($(tail -1 "$LOGD/judgments.log"))"
  log "judgment comment $id ($1): author=$JUDGMENT_AUTHOR on #${meta#* } PASS"
}
check_env_judgment() {
  check_comment "$ENV_JUDGMENT" "$JUDGMENT_ISSUE" env-judgment --repo "$REPO" --main-ref origin/main --kitrel "$KITREL" --kit-dir "$KIT_DIR"
}
# The T1 r01 acceptance (#15 comment 6106366753) predates the record format and has no runId line, so it is accepted
# only as the acceptance of that Run. Every later acceptance must use the record format (judgment line + runId line).
KNOWN_ACCEPT_RUN=EXP-001-train-normalize-name-r01-T1
KNOWN_ACCEPT_ID=6106366753
check_prior_accept() {
  if [ "$PRIOR" = "$KNOWN_ACCEPT_RUN" ]; then
    [ "$PRIOR_ACCEPT" = "$KNOWN_ACCEPT_ID" ] || STOP PROTOCOL "acceptance of $PRIOR must be comment $KNOWN_ACCEPT_ID"
    check_comment "$PRIOR_ACCEPT" "$JUDGMENT_ISSUE" legacy-acceptance
  else
    check_comment "$PRIOR_ACCEPT" any run-acceptance --run-id "$PRIOR"
  fi
}
# Container-side codex process control. $1 = check | TERM | KILL. rc 0 = matched (alive / signaled), 1 = none, 2 = cannot determine.
PROC_CTL='mode=$1; pat="/cx/bin/codex exec"
if command -v pgrep >/dev/null 2>&1 && command -v pkill >/dev/null 2>&1; then
  if [ "$mode" = check ]; then pgrep -f "$pat" >/dev/null; rc=$?; else pkill -"$mode" -f "$pat"; rc=$?; fi
  [ "$rc" -le 1 ] && exit "$rc"; exit 2
fi
[ -r /proc/1/cmdline ] || exit 2
found=1
for f in /proc/[0-9]*/cmdline; do
  c=$(tr "\000" " " < "$f" 2>/dev/null) || continue
  case "$c" in "$pat "*|"$pat") found=0; p=${f#/proc/}; p=${p%/cmdline}; [ "$mode" = check ] || kill -"$mode" "$p" 2>/dev/null ;; esac
done
exit "$found"'
proc_ctl() { local rc=0; docker exec "$CNAME" sh -c "$PROC_CTL" proc-ctl "$1" || rc=$?; [ "$rc" -le 2 ] || rc=2; return "$rc"; }
codex_halt() { # 0 = confirmed no codex process, 1 = could not confirm
  local r
  proc_ctl check; r=$?; log "codex process check: rc=$r"; [ "$r" = 1 ] && return 0; [ "$r" = 2 ] && return 1
  proc_ctl TERM; log "sent TERM rc=$?"; sleep 5
  proc_ctl check; r=$?; log "codex process check after TERM: rc=$r"; [ "$r" = 1 ] && return 0; [ "$r" = 2 ] && return 1
  proc_ctl KILL; log "sent KILL rc=$?"; sleep 3
  proc_ctl check; r=$?; log "codex process check after KILL: rc=$r"; [ "$r" = 1 ] && return 0
  return 1
}
SECRET_PATTERNS=('(access|refresh|id)_token' 'eyJ[A-Za-z0-9_-]{10,}' '(^|[^A-Za-z0-9])sk-[A-Za-z0-9_-]{16,}' 'Bearer [A-Za-z0-9._~+/=-]+' '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
secret_scan() { # counts only; 0 = clean, 1 = hit, 2 = scan error
  local i=0 hit=0 files rc n pat
  for pat in "${SECRET_PATTERNS[@]}"; do
    i=$((i + 1)); rc=0
    files=$(LC_ALL=C grep -rEal -e "$pat" "$@") || rc=$?
    [ "$rc" -le 1 ] || { log "secret-scan pattern#$i: scan error rc=$rc"; return 2; }
    n=0; [ "$rc" -eq 1 ] || n=$(grep -c . <<<"$files")
    log "secret-scan pattern#$i: $n file(s)"
    [ "$n" = 0 ] || hit=1
  done
  return "$hit"
}

# ---------------------------------------------------------------- 0. pre-checks
phase 0-precheck
log "mode=$MODE dry-run=$DRY_RUN practice-model=$PRACTICE_MODEL runId=$RUN_ID workspaceId=$WSID fixture=$FIXTURE RD=$RD container=$CNAME"
command -v timeout >/dev/null || STOP PROTOCOL "timeout not found"
"$PY" --version | grep -q '^Python 3\.12\.' || STOP PROTOCOL "--python is not Python 3.12"
"$PY" -I -c 'import yaml' || STOP PROTOCOL "--python lacks PyYAML"
[ -f "$AUTH_SRC" ] && [ -s "$AUTH_SRC" ] || STOP SAFETY "auth file missing or empty (content is never read)"
out=$(docker ps -aq --filter "name=^${CNAME}\$") || STOP SAFETY "docker ps failed (cannot confirm that $CNAME does not exist)"
[ -z "$out" ] || STOP SAFETY "container $CNAME already exists"
(cd "$KIT_DIR" && shasum -a 256 -c SHA256SUMS) > "$LOGD/kit-sha.log" 2>&1 || STOP PROTOCOL "kit SHA256SUMS mismatch"
out=$(find "$KIT_DIR" -type f) || STOP PROTOCOL "cannot list kit files"
n=$(grep -c . "$KIT_DIR/SHA256SUMS") || STOP PROTOCOL "cannot read kit SHA256SUMS"
[ "$(grep -c . <<<"$out" || true)" = "$((n + 1))" ] || STOP PROTOCOL "kit has files not listed in SHA256SUMS"
git -C "$REPO" fetch --quiet origin || STOP PROTOCOL "git fetch origin failed"
KIT_ON_MAIN=1
while IFS= read -r line; do
  f=${line#*  }
  git -C "$REPO" show "origin/main:$KITREL/$f" 2>/dev/null | cmp -s - "$KIT_DIR/$f" || KIT_ON_MAIN=0
done < "$KIT_DIR/SHA256SUMS"
git -C "$REPO" show "origin/main:$KITREL/SHA256SUMS" 2>/dev/null | cmp -s - "$KIT_DIR/SHA256SUMS" || KIT_ON_MAIN=0
if [ "$KIT_ON_MAIN" = 1 ]; then log "kit is byte-identical to origin/main:$KITREL"
elif [ "$MODE" = real ]; then STOP PROTOCOL "kit differs from origin/main:$KITREL (only the merged, reviewed kit may run a matrix Run)"
else log "kit differs from origin/main (practice: allowed, recorded)"; fi

# ---------------------------------------------------------------- 1. configuration check (environment disposition)
phase env-check
[ "$(docker context show)" = "$DOCKER_CONTEXT" ] || ENV_MISMATCH "docker context is not $DOCKER_CONTEXT"
v=$(docker version --format '{{.Server.Version}}') || STOP PROTOCOL "docker version failed"
[ "$v" = "$DOCKER_SERVER_VERSION" ] || ENV_MISMATCH "docker server version $v"
v=$(docker info --format '{{.KernelVersion}}|{{.Architecture}}|{{.OperatingSystem}}') || STOP PROTOCOL "docker info failed"
[ "$v" = "$DOCKER_KERNEL|$DOCKER_ARCH|$DOCKER_OS" ] || ENV_MISMATCH "docker kernel/arch/os: $v"
docker image inspect --format '{{range .RepoDigests}}{{println .}}{{end}}' "$IMAGE" > "$LOGD/image-digests.log" || ENV_MISMATCH "image $IMAGE not present locally"
need "$IMAGE" "$LOGD/image-digests.log"
[ "$(docker image inspect --format '{{.Architecture}}' "$IMAGE")" = "$IMAGE_ARCH" ] || ENV_MISMATCH "image architecture"
[ -x "$CODEX_DIR/bin/codex" ] || ENV_MISMATCH "CODEX_DIR/bin/codex missing"
[ "$(sha "$CODEX_DIR/bin/codex")" = "$CODEX_BIN_SHA256" ] || ENV_MISMATCH "codex binary SHA-256"
gates codex-package --dir "$CODEX_DIR" --version "$CODEX_PACKAGE_VERSION" --target "$CODEX_TARGET" >> "$STATUS_LOG" || ENV_MISMATCH "codex package version/target"
[ "$(sha "$KIT_DIR/container/g.sh")" = "$G_SHA256" ] || ENV_MISMATCH "(g) block SHA-256"
grep -qxF -- "$LAUNCH_LINE" "$KIT_DIR/container/g.sh" || ENV_MISMATCH "(g) launch line"
[ "$(sha "$KIT_DIR/container/config-never.sh")" = "$CONFIG_SCRIPT_SHA256" ] || ENV_MISMATCH "config script SHA-256"
sed -n '/^cat > /,/^EOF$/p' "$KIT_DIR/container/config-never.sh" | sed '1d;$d' > "$GEN/config.toml"
[ "$(sha "$GEN/config.toml")" = "$CONFIG_TOML_SHA256" ] || ENV_MISMATCH "config.toml bytes"
log "configuration check PASS: context=$DOCKER_CONTEXT server=$DOCKER_SERVER_VERSION kernel=$DOCKER_KERNEL image=$IMAGE codex=$CODEX_PACKAGE_VERSION/$CODEX_BIN_SHA256 config=$CONFIG_TOML_SHA256 (g)=$G_SHA256"
if [ "$MODE" = real ]; then
  check_env_judgment
else
  log "environment Judgment comment: N/A (practice)"
fi

# ---------------------------------------------------------------- 2. clean isolated checkout (Gate 4)
phase gate1-5
git -C "$REPO" worktree add --detach "$WT" origin/main >/dev/null 2>&1 || STOP PROTOCOL "worktree add failed"
MAIN_SHA=$(git -C "$WT" rev-parse HEAD)
log "checkout $WT at origin/main $MAIN_SHA"
out=$(git -C "$WT" status --porcelain=v1 --untracked-files=all) || STOP PROTOCOL "Gate 4: git status failed"
[ -z "$out" ] || STOP PROTOCOL "Gate 4: checkout not clean"
[ ! -e "$WS" ] || STOP PROTOCOL "Gate 4: workspace exists"
cd "$WT"
"$PY" -B scripts/validate_experiment_freeze.py > "$LOGD/gate1.log" 2>&1 || STOP PROTOCOL "Gate 1: Feature Freeze validation"
log "Gate 1 PASS (Feature Freeze)"
SECCOMP=$WT/$SECCOMP_REL
[ "$(sha "$SECCOMP")" = "$SECCOMP_SHA256" ] || ENV_MISMATCH "seccomp SHA-256"
if [ "$MODE" = real ]; then
  PRIOR=$(gates matrix-order --root "$WT" --run-id "$RUN_ID") || STOP PROTOCOL "Gate 2/3: matrix order ($PRIOR)"
  "$PY" -B scripts/validate_pilot.py --pilot "$PILOT_REL/pilot.yaml" --matrix "$PILOT_REL/run-matrix.yaml" --run-id "$PRIOR" > "$LOGD/gate2.log" 2>&1 || STOP PROTOCOL "Gate 2: prior Run $PRIOR single-run validation"
  check_prior_accept
  log "Gate 2 PASS (prior $PRIOR validated and accepted) / Gate 3 PASS (slot never attempted, no failure archive)"
  gates workspace-id --root "$WT" --workspace-id "$WSID" >> "$STATUS_LOG" || STOP PROTOCOL "Gate 5: workspaceId"
else
  log "Gate 2/3: N/A (practice task is not a matrix slot)"
  [[ $WSID =~ ^[a-z0-9][a-z0-9-]{7,95}$ ]] || STOP PROTOCOL "Gate 5: workspaceId format"
fi
log "Gate 4 PASS / Gate 5 PASS"

# ---------------------------------------------------------------- 3. prepare (Gate 6) and Gates 7-9
phase gate6-9
if [ "$MODE" = real ]; then
  if [ "$ATTEMPTS" != 0 ]; then
    check_comment "$SLOT_DISP" "$JUDGMENT_ISSUE" slot-disposition --run-id "$RUN_ID" --attempt "$((ATTEMPTS + 1))"
  fi
  ATTEMPT_DIR=$(gates reserve-attempt --registry "$ATTEMPT_REGISTRY" --run-id "$RUN_ID" --expect-existing "$ATTEMPTS") || STOP PROTOCOL "attempt reservation: $ATTEMPT_DIR"
  printf 'run-dir: %s\ndry-run: %s\nslot-disposition: %s\n' "$RD" "$DRY_RUN" "${SLOT_DISP:-none}" > "$ATTEMPT_DIR/record"
  log "attempt $((ATTEMPTS + 1)) of $RUN_ID reserved at $ATTEMPT_DIR (kept even if this attempt STOPs or is a dry-run)"
  git diff --quiet origin/main -- scripts/prepare_pilot_run.py || STOP PROTOCOL "Gate 6: prepare_pilot_run.py differs from origin/main"
  "$PY" -B scripts/prepare_pilot_run.py --pilot "$PILOT_REL/pilot.yaml" --matrix "$PILOT_REL/run-matrix.yaml" \
    --run-id "$RUN_ID" --workspace "$WS" --workspace-id "$WSID" > "$LOGD/gate6.log" 2>&1 || STOP PROTOCOL "Gate 6: prepare_pilot_run.py failed"
  RUN_META=$WT/$ARTIFACT_ROOT/$RUN_ID/run-meta.yaml
  PROMPT_SRC=$WT/$ARTIFACT_ROOT/$RUN_ID/prompt.md
  out=$(git status --porcelain=v1 --untracked-files=all) || STOP PROTOCOL "Gate 6: git status failed"
  [ "$(LC_ALL=C sort <<<"$out" | tr '\n' '|')" = "?? $ARTIFACT_ROOT/$RUN_ID/prompt.md|?? $ARTIFACT_ROOT/$RUN_ID/run-meta.yaml|" ] || STOP PROTOCOL "Gate 6: prepare changed more than the run directory"
  FIX_DIR=$WT/$FIXTURE
else
  PREP=$RD/practice-prep
  mkdir -m 700 "$PREP"
  gates practice-meta --template "$KIT_DIR/rehearsal/run-meta.yaml" --workspace-id "$WSID" --out "$PREP/run-meta.yaml" >> "$STATUS_LOG" || STOP PROTOCOL "Gate 6: practice run-meta"
  cp "$KIT_DIR/rehearsal/prompt.md" "$PREP/prompt.md"
  cp -R "$KIT_DIR/rehearsal/fixture" "$WS"
  RUN_META=$PREP/run-meta.yaml
  PROMPT_SRC=$PREP/prompt.md
  FIX_DIR=$KIT_DIR/rehearsal/fixture
fi
log "Gate 6 PASS (prepared; workspace $WS)"
META_OUT=$(gates meta --root "$WT" --run-meta "$RUN_META" --prompt "$PROMPT_SRC" --run-id "$RUN_ID" --workspace-id "$WSID" \
  --fixture "$FIXTURE" --expectations "$KIT_DIR/expectations/gate11.tsv" --mode "$MODE") || STOP PROTOCOL "Gate 7/8: $META_OUT"
SCENARIO=$(sed -n 's/^scenario=//p' <<<"$META_OUT")
PROMPT_SHA=$(sed -n 's/^promptSha256=//p' <<<"$META_OUT")
[ -n "$SCENARIO" ] && [[ $PROMPT_SHA =~ ^[0-9a-f]{64}$ ]] || STOP PROTOCOL "Gate 7/8: scenario / prompt SHA-256 not determined"
log "Gate 7 PASS (prompt SHA-256 $PROMPT_SHA = run-meta promptSha256) / Gate 8 PASS (metadata; scenario $SCENARIO)"
diff -r "$FIX_DIR" "$WS" > "$LOGD/gate9-diff.log" || STOP PROTOCOL "Gate 9: workspace differs from fixture"
hashes "$FIX_DIR" > "$LOGD/fixture.sha256" || STOP PROTOCOL "Gate 9: cannot hash fixture"
hashes "$WS" > "$LOGD/ws-gate9.sha256" || STOP PROTOCOL "Gate 9: cannot hash workspace"
cmp -s "$LOGD/fixture.sha256" "$LOGD/ws-gate9.sha256" || STOP PROTOCOL "Gate 9: file set / SHA-256"
gates fixture-hashes --table "$KIT_DIR/expectations/fixtures.sha256" --scenario "$SCENARIO" --observed "$LOGD/ws-gate9.sha256" >> "$STATUS_LOG" || STOP PROTOCOL "Gate 9: recorded fixture hashes"
log "Gate 9 PASS"

# ---------------------------------------------------------------- 4. Run-specific rendering, PROMPT copy outside runs/, static bind audit
phase render
EXPECT=()
while IFS= read -r l; do EXPECT+=("$l"); done < <(gates expect --expectations "$KIT_DIR/expectations/gate11.tsv" --scenario "$SCENARIO")
[ "${#EXPECT[@]}" = 6 ] || STOP PROTOCOL "Gate 11 expectation for $SCENARIO not determined"
render "$KIT_DIR/container/nonmodel-1-5.sh.in" "$GEN/nonmodel-1-5.sh" "${EXPECT[@]}" || STOP PROTOCOL "render nonmodel-1-5.sh"
render "$KIT_DIR/container/preflight-d.sh.in" "$GEN/preflight-d.sh" "PROMPT_SHA256=$PROMPT_SHA" || STOP PROTOCOL "render preflight-d.sh"
render "$KIT_DIR/host/host-mounts.sh.in" "$GEN/host-mounts.sh" "PROMPT_SHA256=$PROMPT_SHA" || STOP PROTOCOL "render host-mounts.sh"
render "$KIT_DIR/host/prompt-copy.sh.in" "$GEN/prompt-copy.sh" "PROMPT_SHA256=$PROMPT_SHA" || STOP PROTOCOL "render prompt-copy.sh"
cp "$KIT_DIR/container/proc-check.sh" "$GEN/proc-check.sh"
for n in nonmodel-1-5.sh preflight-d.sh host-mounts.sh prompt-copy.sh proc-check.sh; do log "rendered $n sha256 $(sha "$GEN/$n")"; done
log "Gate 11 expectation ($SCENARIO): ${EXPECT[*]}"
PROMPT_SRC="$PROMPT_SRC" RUN_INPUT="$RUN_INPUT" bash -c '. "$1"' _ "$GEN/prompt-copy.sh" > "$LOGD/prompt-copy.log" 2>&1 || STOP PROTOCOL "prompt copy / SHA-256"
PROMPT=$RUN_INPUT/prompt.md
[ "$(sha "$PROMPT")" = "$PROMPT_SHA" ] || STOP PROTOCOL "PROMPT copy SHA-256"
gates bind-audit --root "$WT" --workspace "$WS" --prompt "$PROMPT" --codex-dir "$CODEX_DIR" --seccomp "$SECCOMP" \
  --auth-file "$AUTH_SRC" --prompt-sha "$PROMPT_SHA" > "$LOGD/bind-audit.log" 2>&1 || STOP SAFETY "static bind-source audit"
log "PROMPT copy + static bind audit PASS"

# ---------------------------------------------------------------- 5. (a) container
phase a-container
CONTAINER_UP=1   # set before run: a partially created container must also go through stop_container
docker run --rm -dit \
  --name "$CNAME" \
  --platform linux/arm64 \
  --security-opt seccomp="$SECCOMP" \
  --security-opt no-new-privileges \
  --cap-drop ALL \
  --user "$(id -u):$(id -g)" \
  --read-only --tmpfs /tmp \
  --tmpfs /tmp/codex-home:uid="$(id -u)",gid="$(id -g)",mode=700 \
  -e HOME=/tmp/home \
  -e CODEX_HOME=/tmp/codex-home \
  -v "$AUTH_SRC":/tmp/codex-home/auth.json:ro \
  -v "$CODEX_DIR":/cx:ro \
  -v "$PROMPT":/run-input/prompt.md:ro \
  -v "$WS":/work -w /work \
  "$IMAGE" \
  bash -l > /dev/null || STOP SAFETY "docker run failed"
log "container up"
docker inspect --format 'Privileged={{.HostConfig.Privileged}} CapAdd={{json .HostConfig.CapAdd}} CapDrop={{json .HostConfig.CapDrop}} ReadonlyRootfs={{.HostConfig.ReadonlyRootfs}} User={{.Config.User}} Image={{.Config.Image}}' "$CNAME" > "$LOGD/inspect.log"
need "Privileged=false CapAdd=null CapDrop=[\"ALL\"] ReadonlyRootfs=true User=$(id -u):$(id -g) Image=$IMAGE" "$LOGD/inspect.log"
docker inspect --format '{{range .HostConfig.SecurityOpt}}{{println .}}{{end}}' "$CNAME" > "$LOGD/security-opt.log"
need no-new-privileges "$LOGD/security-opt.log"
grep -q '^seccomp=' "$LOGD/security-opt.log" || STOP SAFETY "seccomp security option missing"
if grep -q 'unconfined' "$LOGD/security-opt.log"; then STOP SAFETY "unconfined security option"; fi
log "container constraints PASS"

# ---------------------------------------------------------------- 6. place scripts + sha
phase place
for n in nonmodel-1-5.sh preflight-d.sh proc-check.sh; do
  docker exec -i "$CNAME" sh -c "cat > /tmp/$n" < "$GEN/$n"
  c=$(docker exec "$CNAME" sha256sum "/tmp/$n" | cut -c1-64)
  [ "$c" = "$(sha "$GEN/$n")" ] || STOP PROTOCOL "placement SHA-256 mismatch: $n"
  log "placed $n sha=$c"
done

# ---------------------------------------------------------------- 7. (b)(c)
phase bc
{ echo 'set -euo pipefail'; echo 'mkdir -p "$HOME" "$CODEX_HOME"'; cat "$KIT_DIR/container/config-never.sh"; echo 'echo b-c-done'; } > "$GEN/bc.sh"
inexec "$GEN/bc.sh" > "$LOGD/bc.log" 2>&1 || STOP PROTOCOL "(b)(c)"
need b-c-done "$LOGD/bc.log"
c=$(docker exec "$CNAME" sh -c 'sha256sum "$CODEX_HOME/config.toml"' | cut -c1-64)
[ "$c" = "$CONFIG_TOML_SHA256" ] || ENV_MISMATCH "config.toml in container"
log "config.toml in container sha256 $c"

# ---------------------------------------------------------------- 8. (d) all checks
phase d1-nonmodel  # Gate 10/11
printf 'cd /work\nbash /tmp/nonmodel-1-5.sh\n' > "$GEN/d1.sh"
inexec "$GEN/d1.sh" > "$LOGD/d1.log" 2>&1 || STOP PROTOCOL "nonmodel-1-5 (Gate 10/11)"
PASS11=$(sed -n 's/^echo "\(PASS: Gate 10\/11 .*\)"$/\1/p' "$GEN/nonmodel-1-5.sh")
[ -n "$PASS11" ] || STOP PROTOCOL "Gate 11 PASS line not determined"
need "$PASS11" "$LOGD/d1.log"
grep -q "^Linux .* $DOCKER_KERNEL " "$LOGD/d1.log" || ENV_MISMATCH "container kernel is not $DOCKER_KERNEL"
log "Gate 10 PASS / Gate 11 PASS ($PASS11)"
phase d2-preflight  # version, login, config, doctor, prompt sha, auth not readable, env keys, /run-input
printf 'cd /work\nbash /tmp/preflight-d.sh\n' > "$GEN/d2.sh"
inexec "$GEN/d2.sh" > "$LOGD/d2.log" 2>&1 || STOP SAFETY "preflight-d"
need "$CODEX_VERSION_LINE" "$LOGD/d2.log"
need 'PASS: logged in using ChatGPT' "$LOGD/d2.log"
need 'PASS: doctor lines' "$LOGD/d2.log"
need 'PASS: prompt SHA-256' "$LOGD/d2.log"
need 'PASS: auth file exists (container side) and is not readable inside sandbox' "$LOGD/d2.log"
need 'PASS: no auth-like env keys in container shell (GPG_KEY image default allowed)' "$LOGD/d2.log"
need 'PASS: no auth-like env keys inside sandbox (GPG_KEY image default allowed)' "$LOGD/d2.log"
need 'PASS: preflight (d) container checks complete' "$LOGD/d2.log"
log "preflight-d PASS (auth isolation, login, doctor, env keys, /run-input)"
phase d3-proc
printf 'cd /work\nbash /tmp/proc-check.sh\n' > "$GEN/d3.sh"
inexec "$GEN/d3.sh" > "$LOGD/d3.log" 2>&1 || STOP SAFETY "proc-check (/proc reachability of the Codex process)"
[ "$(tail -1 "$LOGD/d3.log" | cut -c1-5)" = "PASS:" ] || STOP SAFETY "proc-check last line is not PASS:"
log "proc-check PASS"
phase gate13
CNAME="$CNAME" WS="$WS" CODEX_DIR="$CODEX_DIR" PROMPT="$PROMPT" AUTH_SRC="$AUTH_SRC" bash "$GEN/host-mounts.sh" > "$LOGD/gate13-mounts.log" 2>&1 || STOP SAFETY "host-mounts (Gate 13 mount audit)"
[ "$(tail -1 "$LOGD/gate13-mounts.log" | cut -c1-5)" = "PASS:" ] || STOP SAFETY "host-mounts last line is not PASS:"
out=$(cd "$WS" && find . -mindepth 1) || STOP PROTOCOL "Gate 13: cannot list workspace"
sed 's|^\.|/work|' <<<"$out" | LC_ALL=C sort > "$LOGD/gate13-ws-expected.txt"
awk '/^\/work(\/|$)/' "$LOGD/d2.log" | grep -vx /work | LC_ALL=C sort > "$LOGD/gate13-ws-container.txt"
cmp -s "$LOGD/gate13-ws-expected.txt" "$LOGD/gate13-ws-container.txt" || STOP PROTOCOL "Gate 13: /work listing differs from fixture set"
log "Gate 13 PASS"
phase gate12
diff -r "$FIX_DIR" "$WS" > "$LOGD/gate12-diff.log" || STOP PROTOCOL "Gate 12: workspace changed during preflight"
hashes "$WS" > "$LOGD/ws-gate12.sha256" || STOP PROTOCOL "Gate 12: cannot hash workspace"
cmp -s "$LOGD/fixture.sha256" "$LOGD/ws-gate12.sha256" || STOP PROTOCOL "Gate 12: file set / SHA-256"
log "Gate 12 PASS"
phase preflight-scan
rc=0; secret_scan "$LOGD" || rc=$?
[ "$rc" = 0 ] || STOP SECRET "secret-like pattern in preflight logs or scan error (rc=$rc; values not printed)"
# (e) reaching this line means every (a)-(d) / Gate 1-13 / configuration check passed

# ---------------------------------------------------------------- 9. (f) last checks
phase f-final
if [ "$MODE" = real ]; then
  git -C "$REPO" fetch --quiet origin || STOP PROTOCOL "git fetch origin failed"
  out=$(git -C "$REPO" ls-tree --name-only "origin/main" "$ARTIFACT_ROOT/$RUN_ID") || STOP PROTOCOL "git ls-tree origin/main failed"
  [ -z "$out" ] || STOP PROTOCOL "origin/main now has a run directory for $RUN_ID"
  check_env_judgment
  check_prior_accept
fi
out=$(docker ps -q --filter "name=^${CNAME}\$") || STOP SAFETY "docker ps failed"
[ -n "$out" ] || STOP SAFETY "container not running"
log "(e)(f) PASS: every preflight check passed"

if [ "$DRY_RUN" = 1 ]; then
  phase dry-run-end
  log "DRY-RUN: stopping right before (g). The model was NOT started; no lock was taken."
  STOP_RC=0
  stop_container || STOP_RC=$?
  {
    echo "=== run-kit-g DRY-RUN summary ==="
    echo "run dir: $RD"
    echo "origin/main: $MAIN_SHA  runId: $RUN_ID  workspaceId: $WSID  scenario: $SCENARIO"
    echo "result: $([ "$STOP_RC" = 0 ] && echo 'PREFLIGHT PASS (model not started)' || echo 'CONTAINER-NOT-STOPPED')"
    echo "container left (docker ps -a): $LEFT"
  } | tee -a "$STATUS_LOG"
  [ "$STOP_RC" = 0 ] || exit 1
  exit 0
fi
[ "$MODE" = real ] || [ "$PRACTICE_MODEL" = 1 ] || STOP PROTOCOL "practice model start requires --practice-model"
mkdir -m 700 -p "$WR/locks"
mkdir "$LOCK" || STOP PROTOCOL "lock acquisition failed (concurrent or prior start)"
printf '%s\n' "$RD" > "$LOCK/run-dir"
log "lock acquired: $LOCK"

# ---------------------------------------------------------------- 10. (g) the only model invocation
phase g-model
trap - ERR
set +e
STARTED_MODEL=1
log "MODEL STARTED FROM HERE (codex exec; host timeout ${TIMEOUT_S}s wraps (g); the Run slot is consumed; never re-run)"
date '+%Y-%m-%dT%H:%M:%S%z' > "$LOCK/host-started-at"
timeout "$TIMEOUT_S" docker exec -i "$CNAME" bash -l < "$KIT_DIR/container/g.sh" > "$RD/codex-stdout.log" 2>&1
HOST_RC=$?
date '+%Y-%m-%dT%H:%M:%S%z' > "$LOCK/host-finished-at"
chmod 600 "$RD/codex-stdout.log"
log "docker exec rc=$HOST_RC"
ABORTS=""
abort_reason() { ABORTS="$ABORTS$1"$'\n'; log "ABORT-REASON: $1"; }
TIMED_OUT=0
HALTED=1
if [ "$HOST_RC" = 124 ]; then
  TIMED_OUT=1
  abort_reason "timeout ${TIMEOUT_S}s (run not completed)"
  if codex_halt; then log "codex process stop confirmed"; else HALTED=0; log "codex process stop NOT confirmed"; fi
fi
FINISHED_AT=$(docker exec "$CNAME" date '+%Y-%m-%dT%H:%M:%S%z' 2>/dev/null)
FIN_RC=$?
STARTED_AT=$(grep -m1 -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}[+-][0-9]{4}$' "$RD/codex-stdout.log")
START_WHY=ok; [ -n "$STARTED_AT" ] || START_WHY="no ISO date line in (g) stdout codex-stdout.log"
END_WHY=ok; [ -n "$FINISHED_AT" ] || END_WHY="separate 'docker exec date' failed (rc=$FIN_RC, empty output)"

# ---------------------------------------------------------------- 11. evidence collection (fail-closed, before docker stop)
phase collect
if [ "$HALTED" = 0 ]; then
  SINK=$RD/quarantine-undetermined
  log "collection goes to $SINK (UNDETERMINED: codex may still be running; not a normal result)"
fi
mkdir -m 700 "$SINK" || log "mkdir SINK failed"
CNAME="$CNAME" SINK="$SINK" bash "$KIT_DIR/host/collect-evidence.sh" > "$LOGD/collect.log" 2>&1
COLLECT_RC=$?
log "collect-evidence rc=$COLLECT_RC (last: $(tail -1 "$LOGD/collect.log" | cut -c1-80))"
[ -n "$STARTED_AT" ] && printf '%s\n' "$STARTED_AT" > "$SINK/started-at"
[ -n "$FINISHED_AT" ] && printf '%s\n' "$FINISHED_AT" > "$SINK/finished-at"
COLLECT_STOP=$(grep -m1 '^STOP: ' "$LOGD/collect.log" | cut -c1-120)
COLLECT_SECRET=0
if [ "$COLLECT_RC" != 0 ]; then
  case $COLLECT_STOP in
    "STOP: secret-like pattern found"*|"STOP: auth.json in evidence.tar"*|"STOP: secret scan failed"*)
      COLLECT_SECRET=1
      [ -f "$SINK/evidence.tar" ] && chmod 600 "$SINK/evidence.tar"
      log "collect-evidence stopped on secret detection (${COLLECT_STOP}) -> HANDLING quarantine; run result unaffected" ;;
    *) abort_reason "required evidence collection failed: collect-evidence rc=$COLLECT_RC (${COLLECT_STOP:-no STOP line})" ;;
  esac
fi
EV_TAR=ok; EV_EXIT_VAL=missing; EXD=""
if [ ! -e "$SINK/evidence.tar" ]; then EV_TAR="evidence.tar not created"
elif [ ! -s "$SINK/evidence.tar" ]; then EV_TAR="evidence.tar is empty"
elif ! EXD=$(mktemp -d "$RD/.evcheck.XXXXXX"); then EV_TAR="cannot create extraction dir"; EXD=""
elif ! tar -xf "$SINK/evidence.tar" -C "$EXD" 2>/dev/null; then EV_TAR="evidence.tar extraction failed (tar -xf)"
fi
[ "$EV_TAR" = ok ] || abort_reason "required evidence collection failed: $EV_TAR"
EV_EXIT=missing; EV_SESSION=missing
if [ "$EV_TAR" = ok ]; then
  [ -f "$EXD/exit-code" ] && [ -s "$EXD/exit-code" ] && { EV_EXIT=recovered; EV_EXIT_VAL=$(head -c 16 "$EXD/exit-code" | tr -dc '0-9-'); }
  [ -n "$(find "$EXD/codex-home/sessions" -type f -size +0 2>/dev/null | head -1)" ] && EV_SESSION=recovered
fi
[ -z "$EXD" ] || rm -rf "$EXD"
EV_START=missing; [ -s "$SINK/started-at" ] && EV_START=recovered
EV_END=missing; [ -s "$SINK/finished-at" ] && EV_END=recovered
log "required evidence: evidence.tar=$EV_TAR exit-code=$EV_EXIT session=$EV_SESSION started-at=$EV_START (g stdout: $START_WHY) finished-at=$EV_END (separate exec: $END_WHY)"
[ "$EV_EXIT" = recovered ] || abort_reason "required evidence not recovered: exit-code (evidence.tar: $EV_TAR)"
[ "$EV_SESSION" = recovered ] || abort_reason "required evidence not recovered: session (evidence.tar: $EV_TAR)"
[ "$EV_START" = recovered ] || abort_reason "required evidence not recovered: started-at ($START_WHY)"
[ "$EV_END" = recovered ] || abort_reason "required evidence not recovered: finished-at ($END_WHY)"
secret_scan "$RD/codex-stdout.log" "$LOGD"
SCAN_RC=$?
HANDLING=none
if [ "$SCAN_RC" != 0 ] || [ "$COLLECT_SECRET" = 1 ]; then
  HANDLING="quarantine — do not attach to Issue (secret scan rc=$SCAN_RC; collect-evidence secret stop=$COLLECT_SECRET; counts only above)"
  log "HANDLING: $HANDLING"
fi

# ---------------------------------------------------------------- 12. stop container
phase stop
STOP_RC=0
stop_container || STOP_RC=$?
log "stop_container rc=$STOP_RC (CONTAINER_STUCK=$CONTAINER_STUCK)"

# ---------------------------------------------------------------- 13. summary
phase summary
if [ "$HALTED" = 0 ]; then RESULT="UNDETERMINED (timeout; codex stop not confirmed; collected files quarantined)"
elif [ -n "$ABORTS" ]; then RESULT="INFRASTRUCTURE ABORT"
else RESULT="COMPLETED"; fi
[ "$STOP_RC" = 0 ] && [ "$CONTAINER_STUCK" = 0 ] || { CONTAINER_STUCK=1; RESULT="CONTAINER-NOT-STOPPED (underlying: $RESULT)"; }
{
  echo "=== run-kit-g summary ==="
  echo "run dir: $RD"
  echo "origin/main: $MAIN_SHA  runId: $RUN_ID  workspaceId: $WSID  scenario: $SCENARIO  (g) sha256: $G_SHA256"
  echo "result: $RESULT"
  echo "timeout: $TIMED_OUT  codex stop confirmed: $HALTED"
  echo "codex exit-code (container): $EV_EXIT_VAL  docker exec rc: $HOST_RC"
  echo "required evidence: exit-code=$EV_EXIT session=$EV_SESSION started-at=$EV_START finished-at=$EV_END"
  echo "started (g stdout date): ${STARTED_AT:-missing ($START_WHY)}  finished (separate container date): ${FINISHED_AT:-missing ($END_WHY)}"
  echo "evidence.tar: $EV_TAR  entries: $(tar -tf "$SINK/evidence.tar" 2>/dev/null | wc -l | tr -d ' ')"
  echo "HANDLING: $HANDLING"
  echo "container left (docker ps -a): $LEFT"
  [ "$CONTAINER_STUCK" = 0 ] || echo "!! auth を bind したコンテナが残存。Operator は直ちに \`docker rm -f $CNAME\` を実行"
} | tee -a "$STATUS_LOG"
case $RESULT in
  COMPLETED) log "DONE: model run finished, required evidence recovered. Next: README「Run 後」"; exit 0 ;;
  *) log "$RESULT. Do NOT re-run this runId. Record per README「Run 後」." ;;
esac
exit 1
