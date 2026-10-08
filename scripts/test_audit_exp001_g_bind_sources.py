#!/usr/bin/env python3
"""Offline negative tests; never read or print credential contents."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "audit_exp001_g_bind_sources.py"
spec = importlib.util.spec_from_file_location("g_sources", PATH)
audit = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(audit)


def main() -> None:
    canonical = ROOT / "experiments/EXP-001-t0-vs-t1/runs/pilot-codex/EXP-001-train-normalize-name-r01-T1/prompt.md"
    seccomp = audit.EXPECTED_SECCOMP_PATH

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        ws = base / "fresh-work"
        ws.mkdir()
        binary_dir = base / "codex"
        (binary_dir / "bin").mkdir(parents=True)
        (binary_dir / "bin" / "codex").write_bytes(b"not executed; existence-only test")
        auth = base / "auth.json"
        auth.write_bytes(b"test-fixture-not-a-credential")
        auth.chmod(0o600)
        assert audit.audit_sources(ws, canonical, binary_dir, seccomp, auth) == []

        def expect(substring: str, *, workspace=ws, prompt=canonical,
                   codex_dir=binary_dir, profile=seccomp, auth_file=auth) -> None:
            failures = audit.audit_sources(workspace, prompt, codex_dir, profile, auth_file)
            assert any(substring in failure for failure in failures), failures

        expect("workspace: must be outside", workspace=ROOT / "scripts")
        expect("source must already exist", workspace=base / "missing")
        wrong_prompt = base / "prompt.md"
        wrong_prompt.write_text("changed")
        expect("SHA-256 mismatch", prompt=wrong_prompt)
        archived_prompt = ROOT / "experiments/EXP-001-t0-vs-t1/runs/infrastructure-failures/EXP-001-train-normalize-name-r01-T1/01a1132a-1de0-70d2-b810-c500b79430c9/prompt.md"
        expect("original failure archive", prompt=archived_prompt)
        wrong_profile = base / "other.json"
        wrong_profile.write_text("{}")
        expect("reviewed repository profile", profile=wrong_profile)
        expect("bin/codex", codex_dir=base)
        expect("outside repository and workspace", auth_file=ROOT / "README.md")
        (ws / "auth.json").write_text("test-only")
        expect("outside repository and workspace", auth_file=ws / "auth.json")
        (ws / "auth.json").unlink()
        ws_link = base / "workspace-link"
        ws_link.symlink_to(ws, target_is_directory=True)
        expect("non-symlink directory", workspace=ws_link)

        auth.chmod(0o644)
        expect("group/other permission")
        auth.chmod(0o600)
        auth.unlink()
        expect("source must already exist", auth_file=auth)

    print("EXP-001 candidate G bind-source audit negative tests passed")


if __name__ == "__main__":
    main()
