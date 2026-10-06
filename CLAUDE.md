# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Claude Code specific

`.claude/settings.json` asks before Edit/Write tool calls on the manifest `experiments/EXP-001-t0-vs-t1/pilot/freeze.yaml` and every file it lists; this does not cover writes through Bash, so CI `validate_experiment_freeze.py` remains the guard. Keep the list in sync when the freeze manifest changes. It also sets `PYTHONDONTWRITEBYTECODE=1` so running fixture tests does not leave `__pycache__` in frozen fixture directories.
