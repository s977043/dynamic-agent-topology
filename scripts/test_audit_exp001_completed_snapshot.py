#!/usr/bin/env python3
"""Negative tests for reviewed EXP-001 completed-snapshot identity."""
from __future__ import annotations

from copy import deepcopy

import yaml

from audit_exp001_completed_snapshot import (
    MANIFEST,
    ORIGINAL_BLOBS,
    audit_snapshot,
)

manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
assert manifest["metadata"]["status"] == "completed"
assert len(ORIGINAL_BLOBS) == 33
assert audit_snapshot(manifest) == [], "unchanged reviewed snapshot must pass"

failures: list[str] = []


def must_fail(name: str, candidate: dict, *, forged_sha=None) -> None:
    errors = audit_snapshot(candidate, **({"blob_sha": forged_sha} if forged_sha else {}))
    if not errors:
        failures.append(name)


changed = deepcopy(manifest)
changed["metadata"]["revision"] = 4
must_fail("revision changed", changed)

changed = deepcopy(manifest)
changed["metadata"]["status"] = "active"
must_fail("active cannot pass completed audit", changed)

changed = deepcopy(manifest)
changed["spec"]["baselineCommit"] = "0" * 40
must_fail("baseline commit changed", changed)

changed = deepcopy(manifest)
changed["spec"]["files"].pop()
must_fail("frozen file missing", changed)

changed = deepcopy(manifest)
changed["spec"]["files"][1] = deepcopy(changed["spec"]["files"][0])
must_fail("duplicate frozen path", changed)

changed = deepcopy(manifest)
changed["spec"]["files"][0]["path"] = "README.md"
must_fail("unreviewed path substitution", changed)

changed = deepcopy(manifest)
changed["spec"]["files"][0]["gitBlobSha"] = "0" * 40
must_fail("manifest SHA changed", changed)

# Attacker-like coupled drift: mutate manifest SHA and make the blob reader
# report the SAME forged value. The independent original baseline must reject.
changed = deepcopy(manifest)
target = changed["spec"]["files"][0]["path"]
changed["spec"]["files"][0]["gitBlobSha"] = "0" * 40
must_fail(
    "manifest and file changed together",
    changed,
    forged_sha=lambda path: "0" * 40 if str(path).endswith(target) else ORIGINAL_BLOBS[path.as_posix().split("/dynamic-agent-topology/")[-1]],
)

if failures:
    raise SystemExit("Snapshot negative tests failed: " + ", ".join(failures))
print("EXP-001 original-snapshot tests passed: matching + 8 negative cases.")
