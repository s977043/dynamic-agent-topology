date '+%Y-%m-%dT%H:%M:%S%z'
rc=0
/cx/bin/codex exec --skip-git-repo-check -C /work - < /run-input/prompt.md || rc=$?
printf '%s\n' "$rc" > /tmp/exit-code
exit "$rc"
