set -euo pipefail
STOP() { echo "STOP: $*"; exit 1; }
has() { local rc=0; grep "$@" || rc=$?; [ "$rc" -le 1 ] || STOP "grep error (rc=$rc)"; return "$rc"; }
CX=/cx/bin/codex
PROBE_OUT=/tmp/proc-probe.txt
# /proc/<pid>/stat の comm は空白や ')' を含み得るため、最後の ') ' 以降を分割する（ppid=2、starttime=20）
stat_field() { local s n=$2 rest; s=$(cat "/proc/$1/stat" 2>/dev/null) || return 1; case $s in *') '*) ;; *) return 1 ;; esac; rest=${s##*) }; set -f; set -- $rest; set +f; [ $# -ge 20 ] || return 1; shift $((n - 1)); printf '%s\n' "$1"; }
# 消えたプロセスは読み飛ばし、存在するのに読めない場合だけ失敗にする
find_codex() { local p=$1 want=$2 e s c pp out
  if ! e=$(readlink "/proc/$p/exe" 2>/dev/null); then [ -e "/proc/$p" ] && return 1; return 0; fi
  if [ "$e" = "$want" ]; then echo "$p"; return 0; fi
  for s in /proc/[0-9]*/stat; do c=${s#/proc/}; c=${c%/stat}
    if ! pp=$(stat_field "$c" 2); then [ -e "/proc/$c" ] && return 1; continue; fi
    if [ "$pp" = "$p" ]; then out=$(find_codex "$c" "$want") || return 1; [ -z "$out" ] || echo "$out"; fi
  done; }
identify_codex() { local cands n
  cands=$(find_codex "$1" "$2") || STOP "cannot read /proc/<pid>/stat or exe while searching from pid $1"
  n=$(grep -c . <<<"$cands" || true)
  [ "$n" = 1 ] || STOP "expected exactly 1 process with exe $2 under pid $1, found ${n:-?}"
  CODEX_PID=$cands
  CODEX_START=$(stat_field "$CODEX_PID" 20) || STOP "cannot read starttime of pid $CODEX_PID"
  CODEX_PPID=$(stat_field "$CODEX_PID" 2) || STOP "cannot read ppid of pid $CODEX_PID"
  echo "PASS: codex pid $CODEX_PID ppid $CODEX_PPID exe $2 starttime $CODEX_START"; }
read -r -d '' PROBE <<'P' || true
set -uo pipefail
sleep 5
echo PROBE_BEGIN
echo "PIDNS $(readlink /proc/self/ns/pid)"
n=0
for p in /proc/[0-9]*; do
  [ "${p#/proc/}" = "$$" ] && { echo "pid $$ self (probe, skipped)"; continue; }
  st=unknown cm=unknown
  if s=$(cat "$p/stat" 2>/dev/null); then case $s in *") "*) cm=${s#*\(}; cm=${cm%\)*}; set -f; set -- ${s##*") "}; set +f; [ $# -ge 20 ] && st=${20} ;; esac; fi
  echo "pid ${p#/proc/} starttime $st comm $cm"
  for f in environ maps; do
    if err=$(head -c1 "$p/$f" 2>&1 >/dev/null); then echo "  BLOCK: $f reachable"
    else case $err in *"Permission denied"*) echo "  $f denied" ;; *) echo "  $f unknown" ;; esac; fi
  done
  if err=$( (exec 3<"$p/mem") 2>&1 ); then echo "  BLOCK: mem reachable"
  else case $err in *"Permission denied"*) echo "  mem denied" ;; *) echo "  mem unknown" ;; esac; fi
  # root/cwd: 外側プロセスの fs 視点をたどれるか（auth.json へのパス経路）
  for f in root cwd; do
    if err=$(ls -A "$p/$f/" 2>&1 >/dev/null); then echo "  BLOCK: $f reachable"
    else case $err in *"Permission denied"*) echo "  $f denied" ;; *) echo "  $f unknown" ;; esac; fi
  done
  # fd: 一覧は同一 uid なら取れる。判定は各エントリの readlink（参照先パス）・open（中身）・fdinfo（pos・flags・ino 等）がすべて Permission denied か（readlink は -v でないとエラー文を出さない）
  if l=$(ls -A "$p/fd" 2>&1); then
    fd=denied fi=denied k=0
    for f in $l; do k=$((k + 1))
      if err=$(readlink -v "$p/fd/$f" 2>&1 >/dev/null); then fd=BLOCK; break; fi
      case $err in *"Permission denied"*) ;; *) fd=unknown ;; esac
      if err=$( (exec 3<"$p/fd/$f") 2>&1 ); then fd=BLOCK; break; fi
      case $err in *"Permission denied"*) ;; *) fd=unknown ;; esac
    done
    for f in $l; do
      if err=$(head -c1 "$p/fdinfo/$f" 2>&1 >/dev/null); then fi=BLOCK; break; fi
      case $err in *"Permission denied"*) ;; *) fi=unknown ;; esac
    done
    [ "$k" -gt 0 ] || { fd=unknown; fi=unknown; }
    case $fd in denied) echo "  fd denied" ;; BLOCK) echo "  BLOCK: fd reachable" ;; *) echo "  fd unknown" ;; esac
    case $fi in denied) echo "  fdinfo denied" ;; BLOCK) echo "  BLOCK: fdinfo reachable" ;; *) echo "  fdinfo unknown" ;; esac
  else case $l in *"Permission denied"*) echo "  fd denied"; echo "  fdinfo denied" ;; *) echo "  fd unknown"; echo "  fdinfo unknown" ;; esac; fi
  n=$((n + 1))
done
echo "PROBE_END entries $n"
P
# timeout 等のラッパーを挟まず起動する（ラッパーと Codex の starttime が同じ clock tick になり対応付けが一意にならないため）
# 同定区間（sleep 1〜identify_codex〜comm/cmdline 読み取り）の時間制限（20 秒）。超過は USR1 で STOP。watchdog は bash（comm が codex でない）なので同定・対応付けに混ざらない
IDENT_LIMIT=20
IDENT_T0=$SECONDS
trap 'STOP "codex identification exceeded ${IDENT_LIMIT}s"' USR1
( sleep "$IDENT_LIMIT"; kill -USR1 $$ 2>/dev/null ) &
IDWATCH=$!
"$CX" sandbox -P t1-workspace -C /work -- bash -lc "$PROBE" > "$PROBE_OUT" 2>&1 &
TARGET=$!
WATCH=
trap 'kill "$TARGET" $IDWATCH $WATCH 2>/dev/null || true' EXIT
sleep 1
# $! 自身の exe が /cx/bin/codex ならそれを、そうでなければ子孫のうち exe が一致する最上位プロセスを候補にする。候補がちょうど 1 つでなければ STOP
identify_codex "$TARGET" "$CX"
CODEX_COMM=$(cat "/proc/$CODEX_PID/comm") || STOP "cannot read comm of pid $CODEX_PID"
mapfile -d '' -t ARGV < "/proc/$CODEX_PID/cmdline" || STOP "cannot read cmdline of pid $CODEX_PID"
echo "comm: $CODEX_COMM argv[0..1]: ${ARGV[0]-} ${ARGV[1]-}"
OWN_NS=$(readlink /proc/self/ns/pid) || STOP "cannot read own pid namespace"
kill "$IDWATCH" 2>/dev/null || true
trap - USR1
IDWATCH=
[ $((SECONDS - IDENT_T0)) -le "$IDENT_LIMIT" ] || STOP "codex identification exceeded ${IDENT_LIMIT}s"
# 時間制限（60 秒）。同定の後に起動し、watchdog 自身が Codex と同じ starttime を持たないようにする
( sleep 60; kill "$TARGET" 2>/dev/null ) &
WATCH=$!
rc=0
wait "$TARGET" || rc=$?
kill "$WATCH" 2>/dev/null || true
trap - EXIT
cat "$PROBE_OUT"
[ "$rc" -ne 143 ] || STOP "sandbox probe killed by 60s watchdog"
[ "$rc" -eq 0 ] || STOP "sandbox probe failed (rc=$rc)"
has -qxF PROBE_BEGIN "$PROBE_OUT" || STOP "probe did not start inside sandbox"
has -Eq '^PROBE_END entries [1-9][0-9]*$' "$PROBE_OUT" || STOP "probe output incomplete"
# 判定は対象エントリ（starttime と comm が一致）だけで行う。probe 自身は除外済み、他プロセスの行は記録のみ
match() { awk -v st="$CODEX_START" -v cm="$CODEX_COMM" -v want="${1-}" '$1 == "pid" && $3 == "starttime" && $4 == st && substr($0, index($0, " comm ") + 6) == cm && (want == "" || $2 == want)' "$PROBE_OUT"; }
n=$(match | grep -c . || true)
[ "$n" = 1 ] || STOP "expected exactly 1 probe entry with starttime $CODEX_START comm $CODEX_COMM, found ${n:-?} (not visible / not mappable)"
if has -qxF "PIDNS $OWN_NS" "$PROBE_OUT"; then [ "$(match "$CODEX_PID" | grep -c . || true)" = 1 ] || STOP "shared pid namespace but pid differs"; fi
key=$(match)
entry=$(awk -v key="$key" '$1 == "pid" { on = ($0 == key); next } $1 == "PROBE_END" { on = 0 } on' "$PROBE_OUT")
printf '%s\n%s\n' "$key" "$entry"
[ "$(grep -c . <<<"$entry" || true)" = 7 ] || STOP "codex entry does not have exactly 7 result lines"
[ "$(grep -cE '^  (environ|maps|mem|root|cwd|fd|fdinfo) denied$' <<<"$entry" || true)" = 7 ] || STOP "codex entry lacks 7 denied lines (unknown or BLOCK)"
echo "PASS: codex pid $CODEX_PID environ/maps/mem/root/cwd denied and every fd entry readlink/open/fdinfo denied from sandbox"
