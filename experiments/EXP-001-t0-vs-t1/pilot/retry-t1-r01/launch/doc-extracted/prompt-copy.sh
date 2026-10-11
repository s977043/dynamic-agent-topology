set -euo pipefail
mkdir -m 700 "$RUN_INPUT"
cp "$PROMPT_SRC" "$RUN_INPUT/prompt.md"
chmod 400 "$RUN_INPUT/prompt.md"
ls -A "$RUN_INPUT"
shasum -a 256 "$RUN_INPUT/prompt.md"
[ "$(shasum -a 256 < "$RUN_INPUT/prompt.md" | cut -c1-64)" = d98fdfb3c56ecc5659466d8b4ba607bb94e77c2a7d74360175b9657b6b93bf86 ]
PROMPT="$RUN_INPUT/prompt.md"
