#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "audit_repository_settings.py"

spec = importlib.util.spec_from_file_location("audit_repository_settings", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def base_target():
    return {
        "kind": "RepositorySettingsTarget",
        "metadata": {"repository": "example/repo"},
        "spec": {
            "description": "desc",
            "homepage": None,
            "topics": ["ai-agents", "evaluation"],
            "features": {"wiki": False, "discussions": False},
            "merge": {
                "squash": True,
                "mergeCommit": False,
                "rebase": False,
                "autoMerge": True,
                "deleteBranchOnMerge": True,
                "updateBranch": True,
                "squashPrTitleDefault": True,
            },
            "defaultBranch": {
                "name": "main",
                "protected": True,
                "activeRulesetRequired": True,
            },
        },
    }


def compliant_repository():
    return {
        "description": "desc",
        "homepage": None,
        "topics": ["ai-agents", "evaluation", "extra-topic"],
        "has_wiki": False,
        "has_discussions": False,
        "allow_squash_merge": True,
        "allow_merge_commit": False,
        "allow_rebase_merge": False,
        "allow_auto_merge": True,
        "delete_branch_on_merge": True,
        "allow_update_branch": True,
        "use_squash_pr_title_as_default": True,
        "default_branch": "main",
    }


def assert_status(checks, name, status):
    actual = next(item["status"] for item in checks if item["name"] == name)
    if actual != status:
        raise AssertionError(f"{name}: expected {status}, got {actual}")


def main() -> int:
    target = base_target()
    repo = compliant_repository()
    branch = {"protected": True}
    rulesets = [{
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
    }]

    checks = module.audit(target, repo, branch, rulesets)
    if any(item["status"] != "PASS" for item in checks):
        raise AssertionError(f"compliant fixture should PASS: {checks}")

    drift_repo = dict(repo)
    drift_repo["description"] = None
    drift_repo["allow_merge_commit"] = True
    drift = module.audit(target, drift_repo, {"protected": False}, [])
    assert_status(drift, "description", "DRIFT")
    assert_status(drift, "merge.mergeCommit", "DRIFT")
    assert_status(drift, "defaultBranch.protected", "DRIFT")
    assert_status(drift, "defaultBranch.activeRulesetRequired", "DRIFT")

    wrong_branch_ruleset = [{
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["refs/heads/release"], "exclude": []}},
    }]
    wrong_branch = module.audit(target, repo, branch, wrong_branch_ruleset)
    assert_status(wrong_branch, "defaultBranch.activeRulesetRequired", "UNKNOWN")

    explicit_other_branch = [{
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["refs/heads/release"], "exclude": ["~DEFAULT_BRANCH"]}},
    }]
    explicit_other = module.audit(target, repo, branch, explicit_other_branch)
    assert_status(explicit_other, "defaultBranch.activeRulesetRequired", "DRIFT")

    unknown = module.audit(
        target,
        repo,
        None,
        None,
        branch_error="HTTP 403",
        rulesets_error="HTTP 403",
    )
    assert_status(unknown, "defaultBranch.protected", "UNKNOWN")
    assert_status(unknown, "defaultBranch.activeRulesetRequired", "UNKNOWN")

    print("Repository settings audit tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
