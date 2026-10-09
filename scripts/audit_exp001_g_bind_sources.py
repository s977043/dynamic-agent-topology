#!/usr/bin/env python3
"""Read-only host-side check of EXP-001 T1 r01 candidate G bind sources.

This deliberately does NOT attest Docker mounts, Codex sandbox behavior,
credentials, runtime parity, or experiment acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PROMPT_SHA256 = "d98fdfb3c56ecc5659466d8b4ba607bb94e77c2a7d74360175b9657b6b93bf86"
EXPECTED_SECCOMP_SHA256 = "085e468fa8e70d8c839a9abab4d74a1ab2abad74a8c26f15234ba62a8ac2e1e8"
EXPECTED_SECCOMP_PATH = ROOT / "experiments/EXP-001-t0-vs-t1/pilot/retry-t1-r01/codex-bwrap-seccomp.json"


def inside(child: Path, parent: Path) -> bool:
    return child == parent or parent in child.parents


def audit_sources(
    workspace: Path, prompt: Path, codex_dir: Path, seccomp: Path, auth_file: Path,
    *, repo_root: Path = ROOT,
) -> list[str]:
    problems: list[str] = []
    sources = {
        "workspace": workspace,
        "prompt": prompt,
        "codex-dir": codex_dir,
        "seccomp": seccomp,
        "auth-file": auth_file,
    }
    for name, path in sources.items():
        if not path.is_absolute():
            problems.append(f"{name}: path must be absolute")
        if not path.exists():
            problems.append(f"{name}: source must already exist (Docker -v can create missing directories)")

    if problems:
        return problems

    repo = repo_root.resolve()
    resolved = {name: path.resolve(strict=True) for name, path in sources.items()}
    ws = resolved["workspace"]

    if not workspace.is_dir() or workspace.is_symlink():
        problems.append("workspace: must be a non-symlink directory")
    if inside(ws, repo):
        problems.append("workspace: must be outside the repository")
    if not prompt.is_file():
        problems.append("prompt: must be an existing regular file")
    if not seccomp.is_file():
        problems.append("seccomp: must be an existing regular file")
    if resolved["seccomp"] != EXPECTED_SECCOMP_PATH.resolve():
        problems.append("seccomp: must be the reviewed repository profile")
    binary = codex_dir / "bin" / "codex"
    if not codex_dir.is_dir() or not binary.is_file():
        problems.append("codex-dir: must contain bin/codex")
    else:
        binary_target = binary.resolve(strict=True)
        if not inside(binary_target, resolved["codex-dir"]):
            problems.append("codex-dir: bin/codex must resolve within the mounted package directory")
    if inside(resolved["codex-dir"], repo):
        problems.append("codex-dir: must be outside the repository and archived attempts")
    if not auth_file.is_file() or auth_file.is_symlink():
        problems.append("auth-file: must be a non-symlink regular file")
    if inside(resolved["auth-file"], repo) or inside(resolved["auth-file"], ws):
        problems.append("auth-file: must be outside repository and workspace")
    if inside(resolved["prompt"], ws) or inside(resolved["codex-dir"], ws):
        problems.append("prompt / codex-dir: must be outside model workspace")
    if inside(ws, resolved["codex-dir"]):
        problems.append("workspace: must not be nested inside the mounted codex package")
    if inside(resolved["auth-file"], resolved["codex-dir"]):
        problems.append("auth-file: must not be exposed through the mounted codex package")
    if inside(resolved["prompt"], repo / "experiments" / "EXP-001-t0-vs-t1" / "runs" / "infrastructure-failures"):
        problems.append("prompt: must not come from the original failure archive")

    if prompt.is_file():
        digest = hashlib.sha256(prompt.read_bytes()).hexdigest()
        if digest != EXPECTED_PROMPT_SHA256:
            problems.append("prompt: frozen SHA-256 mismatch")

    if seccomp.is_file():
        digest = hashlib.sha256(seccomp.read_bytes()).hexdigest()
        if digest != EXPECTED_SECCOMP_SHA256:
            problems.append("seccomp: reviewed SHA-256 mismatch")

    if auth_file.is_file():
        mode = stat.S_IMODE(auth_file.stat().st_mode)
        if mode & 0o077:
            problems.append("auth-file: group/other permission bits must be absent")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--codex-dir", type=Path, required=True)
    parser.add_argument("--seccomp", type=Path, default=EXPECTED_SECCOMP_PATH)
    parser.add_argument("--auth-file", type=Path, required=True)
    args = parser.parse_args()

    failures = audit_sources(
        args.workspace, args.prompt, args.codex_dir, args.seccomp, args.auth_file
    )
    if failures:
        for failure in failures:
            print(f"BLOCK: {failure}", file=sys.stderr)
        return 1
    print("PASS: candidate G host bind sources only (NOT environment/run acceptance)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
