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
[ "$fail" = 0 ] && echo "PASS: selftest" || { echo "STOP: selftest failed"; exit 1; }
