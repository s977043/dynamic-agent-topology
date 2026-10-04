#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

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
                "ruleset": {
                    "required": True,
                    "requirePullRequest": True,
                    "requiredApprovingReviewCountExact": 0,
                    "requireConversationResolution": True,
                    "blockForcePushes": True,
                    "blockDeletion": True,
                    "requiredStatusChecks": ["validate", "Analyze Python"],
                    "requireUpToDate": True,
                },
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


def compliant_ruleset():
    return {
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "rules": [
            {
                "type": "pull_request",
                "parameters": {
                    "required_approving_review_count": 0,
                    "required_review_thread_resolution": True,
                },
            },
            {"type": "non_fast_forward"},
            {"type": "deletion"},
            {
                "type": "required_status_checks",
                "parameters": {
                    "required_status_checks": [
                        {"context": "validate"},
                        {"context": "Analyze Python"},
                        {"context": "extra-check"},
                    ],
                    "strict_required_status_checks_policy": True,
                },
            },
        ],
    }


def assert_status(checks, name, status):
    actual = next(item["status"] for item in checks if item["name"] == name)
    if actual != status:
        raise AssertionError(f"{name}: expected {status}, got {actual}")


def main() -> int:
    target = base_target()
    repo = compliant_repository()
    branch = {"protected": True}

    checks = module.audit(target, repo, branch, [compliant_ruleset()])
    if any(item["status"] != "PASS" for item in checks):
        raise AssertionError(f"compliant fixture should PASS: {checks}")

    no_ruleset = module.audit(target, repo, branch, [])
    for name in (
        "required",
        "requirePullRequest",
        "requiredApprovingReviewCountExact",
        "requireConversationResolution",
        "blockForcePushes",
        "blockDeletion",
        "requiredStatusChecks",
        "requireUpToDate",
    ):
        assert_status(no_ruleset, f"defaultBranch.ruleset.{name}", "DRIFT")

    incomplete = compliant_ruleset()
    incomplete["rules"] = [
        {
            "type": "pull_request",
            "parameters": {
                "required_approving_review_count": 1,
                "required_review_thread_resolution": False,
            },
        },
        {
            "type": "required_status_checks",
            "parameters": {
                "required_status_checks": [{"context": "validate"}],
                "strict_required_status_checks_policy": False,
            },
        },
    ]
    bad = module.audit(target, repo, branch, [incomplete])
    assert_status(bad, "defaultBranch.ruleset.required", "PASS")
    assert_status(bad, "defaultBranch.ruleset.requirePullRequest", "PASS")
    assert_status(bad, "defaultBranch.ruleset.requiredApprovingReviewCount", "DRIFT")
    assert_status(bad, "defaultBranch.ruleset.requireConversationResolution", "DRIFT")
    assert_status(bad, "defaultBranch.ruleset.blockForcePushes", "DRIFT")
    assert_status(bad, "defaultBranch.ruleset.blockDeletion", "DRIFT")
    assert_status(bad, "defaultBranch.ruleset.requiredStatusChecks", "DRIFT")
    assert_status(bad, "defaultBranch.ruleset.requireUpToDate", "DRIFT")

    ambiguous = compliant_ruleset()
    ambiguous["conditions"] = {
        "ref_name": {"include": ["refs/heads/m*"], "exclude": []}
    }
    unknown = module.audit(target, repo, branch, [ambiguous])
    for name in (
        "required",
        "requirePullRequest",
        "requiredApprovingReviewCountExact",
        "requireConversationResolution",
        "blockForcePushes",
        "blockDeletion",
        "requiredStatusChecks",
        "requireUpToDate",
    ):
        assert_status(unknown, f"defaultBranch.ruleset.{name}", "UNKNOWN")

    mixed = [
        compliant_ruleset(),
        {
            "target": "branch",
            "enforcement": "active",
            "conditions": {"ref_name": {"include": ["refs/heads/m*"], "exclude": []}},
            "rules": [],
        },
    ]
    mixed_checks = module.audit(target, repo, branch, mixed)
    assert_status(mixed_checks, "defaultBranch.ruleset.requirePullRequest", "PASS")
    assert_status(mixed_checks, "defaultBranch.ruleset.blockForcePushes", "PASS")
    assert_status(mixed_checks, "defaultBranch.ruleset.requiredApprovingReviewCount", "UNKNOWN")

    unavailable = module.audit(
        target,
        repo,
        None,
        None,
        branch_error="HTTP 403",
        rulesets_error="HTTP 403",
    )
    assert_status(unavailable, "defaultBranch.protected", "UNKNOWN")
    for name in (
        "required",
        "requirePullRequest",
        "requiredApprovingReviewCountExact",
        "requireConversationResolution",
        "blockForcePushes",
        "blockDeletion",
        "requiredStatusChecks",
        "requireUpToDate",
    ):
        assert_status(unavailable, f"defaultBranch.ruleset.{name}", "UNKNOWN")

    print("Repository settings audit tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
