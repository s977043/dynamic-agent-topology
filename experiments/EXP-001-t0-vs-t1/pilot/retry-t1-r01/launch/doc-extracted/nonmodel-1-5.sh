set -euo pipefail
STOP() { echo "STOP: $*"; exit 1; }
has() { local rc=0; grep "$@" || rc=$?; [ "$rc" -le 1 ] || STOP "grep error (rc=$rc)"; return "$rc"; }
echo "== 1 environment"
uname -a
cat /etc/os-release
echo "SHELL=${SHELL-<unset>}"
rc=0
getent passwd "$(id -u)" || rc=$?
case $rc in 0) ;; 2) echo "getent: no passwd entry for uid $(id -u)" ;; *) STOP "getent failed (rc=$rc)" ;; esac
echo "running shell exe: $(readlink /proc/$$/exe)"
command -v bash || STOP "bash not found"
if command -v zsh; then echo "zsh present"; else echo "zsh: not found"; fi
echo "== 2 resolution"
p=$(bash -lc 'command -v python') || STOP "command -v python failed (exit 127 = unresolved)"
case $p in /*) echo "command -v python: $p" ;; *) STOP "python does not resolve to an absolute path: $p" ;; esac
ta=$(bash -lc 'type -a python') || STOP "type -a python failed"
[ -n "$ta" ] || STOP "type -a python printed nothing"
printf '%s\n' "$ta"
if has -qv '^python is /' <<<"$ta"; then STOP "type -a python shows a non-file entry (alias/function/builtin)"; fi
v=$(bash -lc 'python --version' 2>&1) || STOP "python --version failed"
case $v in "Python 3.12."*) echo "$v" ;; *) STOP "unexpected python version: $v" ;; esac
echo "== 3 not a shim/wrapper"
bash -lc 'ls -l "$(command -v python)"' || STOP "ls -l failed"
bash -lc "python -c 'import sys; print(sys.executable); print(sys.version)'" || STOP "python -c failed"
real=$(bash -lc 'readlink -f "$(command -v python)"') || STOP "readlink -f failed"
[ -n "$real" ] || STOP "readlink -f printed nothing"
echo "readlink -f: $real"
hop=$p
while [ -L "$hop" ]; do t=$(readlink "$hop") || STOP "readlink $hop failed"; echo "symlink: $hop -> $t"; case $t in /*) hop=$t ;; *) hop=$(dirname "$hop")/$t ;; esac; done
case $real in *shims*|*.pyenv*|*.asdf*|*venv*) STOP "resolved path looks like a shim/venv: $real" ;; esac
magic=$(od -An -tx1 -N4 "$real" | tr -d ' \n') || STOP "cannot read header of $real"
[ "$magic" = 7f454c46 ] || STOP "$real is not an ELF executable (header $magic)"
echo "ELF header: $magic"
echo "== 4 PATH"
path=$(bash -lc 'printenv PATH') || STOP "printenv PATH failed"
[ -n "$path" ] || STOP "PATH is empty"
echo "PATH=$path"
echo "PASS: steps 1-4 recorded; operator must still attest no rc/PATH/alias/venv changes"
echo "== 5 Gate 10/11 inside Codex sandbox"
rc=0
out=$(timeout 300 /cx/bin/codex sandbox -P t1-workspace -C /work -- bash -lc 'PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests' 2>&1) || rc=$?
printf '%s\n' "$out"
echo "sandbox-test-exit=$rc"
[ "$rc" -ne 124 ] || STOP "sandbox evidence command timed out"
[ "$rc" -eq 1 ] || STOP "expected exit 1 (initial FAIL), got $rc"
if has -Eq 'bwrap:|command not found' <<<"$out"; then STOP "sandbox/launcher error in output"; fi
has -Eq '^Ran 2 tests in ' <<<"$out" || STOP "unittest did not report 'Ran 2 tests'"
has -qxF 'FAILED (failures=1)' <<<"$out" || STOP "unittest did not report exactly 'FAILED (failures=1)'"
[ "$(grep -cE '^(FAIL|ERROR): ' <<<"$out" || true)" = 1 ] || STOP "expected exactly one FAIL/ERROR entry"
has -Eq '^FAIL: test_trims_and_lowercases \(' <<<"$out" || STOP "failing test is not test_trims_and_lowercases"
has -qxF "AssertionError: 'ALICE' != 'alice'" <<<"$out" || STOP "assertion is not 'ALICE' != 'alice'"
echo "PASS: Gate 10/11 python started in sandbox; Ran 2 tests, only test_trims_and_lowercases failed with 'ALICE' != 'alice'"
