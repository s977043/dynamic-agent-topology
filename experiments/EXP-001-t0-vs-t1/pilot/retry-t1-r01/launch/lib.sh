# Sourced by launch.sh / status.sh. Never prints secret values (auth content, env values).
set -Eeuo pipefail
KIT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PHASE=init
STATUS_LOG=/dev/null

log() { printf '%s %s %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "[$PHASE]" "$*" | tee -a "$STATUS_LOG"; }
STOP() { log "STOP: $*"; exit 1; }
phase() { PHASE=$1; log "BEGIN"; }
on_err() { log "STOP: command failed rc=$1 at line $2"; exit "$1"; }
trap 'on_err $? $LINENO' ERR

sha() { shasum -a 256 < "$1" | cut -c1-64; }
perm() { stat -f '%Lp' "$1" 2>/dev/null || stat -c '%a' "$1"; }

# Secret-like patterns (same 5 as doc collect-evidence.sh). Prints counts only.
SECRET_PATTERNS=('(access|refresh|id)_token' 'eyJ[A-Za-z0-9_-]{10,}' '(^|[^A-Za-z0-9])sk-[A-Za-z0-9_-]{16,}' 'Bearer [A-Za-z0-9._~+/=-]+' '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
secret_scan() { # secret_scan <path...> -> 0 if no hit; prints per-pattern file counts
  local i=0 hit=0 files rc n
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
