# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Claude Code specific

`.claude/settings.json` asks before editing any file listed in `experiments/EXP-001-t0-vs-t1/pilot/freeze.yaml`; keep that list in sync when the freeze manifest changes. It also sets `PYTHONDONTWRITEBYTECODE=1` so running fixture tests does not leave `__pycache__` in frozen fixture directories.
