set -euo pipefail
STOP() { echo "STOP: $*"; exit 1; }
has() { local rc=0; grep "$@" || rc=$?; [ "$rc" -le 1 ] || STOP "grep error (rc=$rc)"; return "$rc"; }
: "${CNAME:?}" "${SINK:?}"
[ -d "$SINK" ] || STOP "sink directory does not exist"
umask 077
perm() { stat -f '%Lp %u' "$1" 2>/dev/null || stat -c '%a %u' "$1"; }
[ "$(perm "$SINK")" = "700 $(id -u)" ] || STOP "SINK must be mode 700 and owned by the operator"
out="$SINK/evidence.tar"
[ ! -e "$out" ] || STOP "$out already exists"
docker exec "$CNAME" tar -C /tmp -cf - codex-home/sessions exit-code > "$out" || STOP "docker exec tar failed"
[ -s "$out" ] || STOP "evidence.tar is empty"
list=$(tar -tf "$out") || STOP "evidence.tar is not a readable tar"
printf '%s\n' "$list"
has -qx 'exit-code' <<<"$list" || STOP "exit-code missing"
has -Eq '^codex-home/sessions/.+[^/]$' <<<"$list" || STOP "no session files"
if has -q 'auth\.json' <<<"$list"; then STOP "auth.json in evidence.tar"; fi
chmod 600 "$out" || STOP "chmod 600 failed"
[ "$(perm "$out")" = "600 $(id -u)" ] || STOP "evidence.tar must be mode 600 and owned by the operator"
scan=$(mktemp -d "$SINK/.scan.XXXXXX") || STOP "mktemp failed"
trap 'rm -rf "$scan"' EXIT
tar -xf "$out" -C "$scan" || STOP "cannot extract evidence.tar for scanning"
# 値は出力せず、パターンごとの該当ファイル数だけを出す
found=0
for pat in '(access|refresh|id)_token' 'eyJ[A-Za-z0-9_-]{10,}' '(^|[^A-Za-z0-9])sk-[A-Za-z0-9_-]{16,}' 'Bearer [A-Za-z0-9._~+/=-]+' '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'; do
  rc=0
  files=$(LC_ALL=C grep -rEal -e "$pat" "$scan") || rc=$?
  [ "$rc" -le 1 ] || STOP "secret scan failed (rc=$rc)"
  n=0
  [ "$rc" -eq 1 ] || n=$(grep -c . <<<"$files")
  echo "secret-scan pattern#$((found + 1)): $n file(s)"
  [ "$n" = 0 ] || { echo "STOP: secret-like pattern found ($n file(s)); values not printed"; exit 1; }
  found=$((found + 1))
done
echo "PASS: evidence.tar (600, SINK 700) contains session files and exit-code, no auth.json, no secret-like patterns"
