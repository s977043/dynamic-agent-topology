#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = ROOT / ".github" / "repository-settings-target.yaml"
API_VERSION = "2022-11-28"


def fetch_json(url: str, token: str | None) -> tuple[Any | None, str | None]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "dynamic-agent-topology-repository-audit",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request(url, headers=headers), timeout=20) as response:
            return json.load(response), None
    except HTTPError as error:
        return None, f"HTTP {error.code}"
    except OSError as error:
        return None, str(error)


def load_target(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data.get("kind") != "RepositorySettingsTarget":
        raise ValueError("target kind must be RepositorySettingsTarget")
    return data


def add_check(
    checks: list[dict[str, str]],
    name: str,
    expected: Any,
    actual: Any,
    *,
    comparator=None,
) -> None:
    matches = comparator(expected, actual) if comparator else expected == actual
    checks.append({
        "name": name,
        "status": "PASS" if matches else "DRIFT",
        "expected": json.dumps(expected, ensure_ascii=False, sort_keys=True),
        "actual": json.dumps(actual, ensure_ascii=False, sort_keys=True),
    })


def add_unknown(checks: list[dict[str, str]], name: str, expected: Any, reason: str) -> None:
    checks.append({
        "name": name,
        "status": "UNKNOWN",
        "expected": json.dumps(expected, ensure_ascii=False, sort_keys=True),
        "actual": reason,
    })


def unresolved_ref_pattern(value: Any) -> bool:
    if not isinstance(value, str):
        return True
    if value.startswith("~"):
        return value not in {"~ALL", "~DEFAULT_BRANCH"}
    return any(char in value for char in "*?[")


def ruleset_targets_default_branch(ruleset: dict[str, Any], branch_name: str) -> bool | None:
    ref = f"refs/heads/{branch_name}"
    ref_condition = ruleset.get("conditions", {}).get("ref_name")
    if not isinstance(ref_condition, dict):
        return None

    includes = ref_condition.get("include", [])
    excludes = ref_condition.get("exclude", [])
    if not isinstance(includes, list) or not isinstance(excludes, list):
        return None

    matching_tokens = {"~ALL", "~DEFAULT_BRANCH", ref}
    if any(item in matching_tokens for item in excludes):
        return False

    unknown_exclude = any(unresolved_ref_pattern(item) for item in excludes)
    if any(item in matching_tokens for item in includes):
        return None if unknown_exclude else True

    if not includes:
        return False

    if all(isinstance(item, str) and not unresolved_ref_pattern(item) for item in includes):
        return False

    return None


def applicable_rulesets(
    rulesets: list[dict[str, Any]],
    branch_name: str,
) -> tuple[list[dict[str, Any]], bool]:
    known: list[dict[str, Any]] = []
    unknown = False
    for ruleset in rulesets:
        if ruleset.get("target") != "branch" or ruleset.get("enforcement") != "active":
            continue
        applies = ruleset_targets_default_branch(ruleset, branch_name)
        if applies is True:
            known.append(ruleset)
        elif applies is None:
            unknown = True
    return known, unknown


def rules_of_type(rulesets: list[dict[str, Any]], rule_type: str) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for ruleset in rulesets:
        rules = ruleset.get("rules", [])
        if not isinstance(rules, list):
            continue
        found.extend(
            rule for rule in rules
            if isinstance(rule, dict) and rule.get("type") == rule_type
        )
    return found


def add_positive_ruleset_check(
    checks: list[dict[str, str]],
    name: str,
    expected: bool,
    actual: bool,
    unknown_applicability: bool,
) -> None:
    if actual:
        add_check(checks, name, expected, True)
    elif unknown_applicability:
        add_unknown(checks, name, expected, "an active ruleset may apply through an unresolved ref pattern")
    else:
        add_check(checks, name, expected, False)


def audit_ruleset_semantics(
    checks: list[dict[str, str]],
    target: dict[str, Any],
    rulesets: list[dict[str, Any]] | None,
    branch_name: str,
    rulesets_error: str | None,
) -> None:
    requirement = target["spec"]["defaultBranch"]["ruleset"]
    names = [
        "required",
        "requirePullRequest",
        "requiredApprovingReviewCountExact",
        "requireConversationResolution",
        "blockForcePushes",
        "blockDeletion",
        "requiredStatusChecks",
        "requireUpToDate",
    ]
    prefix = "defaultBranch.ruleset."

    if rulesets is None:
        for name in names:
            add_unknown(checks, prefix + name, requirement[name], rulesets_error or "unavailable")
        return

    applicable, unknown_applicability = applicable_rulesets(rulesets, branch_name)
    if applicable:
        add_check(checks, prefix + "required", requirement["required"], True)
    elif unknown_applicability:
        add_unknown(
            checks,
            prefix + "required",
            requirement["required"],
            "active branch ruleset exists but default-branch applicability is not provable",
        )
    else:
        add_check(checks, prefix + "required", requirement["required"], False)

    pull_rules = rules_of_type(applicable, "pull_request")
    add_positive_ruleset_check(
        checks,
        prefix + "requirePullRequest",
        requirement["requirePullRequest"],
        bool(pull_rules),
        unknown_applicability,
    )

    approval_values: list[int] = []
    approval_unknown = False
    for rule in pull_rules:
        value = rule.get("parameters", {}).get("required_approving_review_count")
        if isinstance(value, int):
            approval_values.append(value)
        else:
            approval_unknown = True
    if pull_rules and approval_values and not approval_unknown and not unknown_applicability:
        add_check(
            checks,
            prefix + "requiredApprovingReviewCountExact",
            requirement["requiredApprovingReviewCountExact"],
            max(approval_values),
        )
    elif not pull_rules and not unknown_applicability:
        add_check(
            checks,
            prefix + "requiredApprovingReviewCountExact",
            requirement["requiredApprovingReviewCountExact"],
            None,
        )
    else:
        add_unknown(
            checks,
            prefix + "requiredApprovingReviewCountExact",
            requirement["requiredApprovingReviewCountExact"],
            "approval requirement cannot be proven across all applicable rulesets",
        )

    thread_values = [
        rule.get("parameters", {}).get("required_review_thread_resolution")
        for rule in pull_rules
    ]
    thread_required = any(value is True for value in thread_values)
    thread_unknown = any(value is None for value in thread_values)
    if thread_required:
        add_check(checks, prefix + "requireConversationResolution", requirement["requireConversationResolution"], True)
    elif thread_unknown or unknown_applicability:
        add_unknown(
            checks,
            prefix + "requireConversationResolution",
            requirement["requireConversationResolution"],
            "review-thread requirement cannot be proven",
        )
    else:
        add_check(checks, prefix + "requireConversationResolution", requirement["requireConversationResolution"], False)

    add_positive_ruleset_check(
        checks,
        prefix + "blockForcePushes",
        requirement["blockForcePushes"],
        bool(rules_of_type(applicable, "non_fast_forward")),
        unknown_applicability,
    )
    add_positive_ruleset_check(
        checks,
        prefix + "blockDeletion",
        requirement["blockDeletion"],
        bool(rules_of_type(applicable, "deletion")),
        unknown_applicability,
    )

    status_rules = rules_of_type(applicable, "required_status_checks")
    contexts: set[str] = set()
    status_unknown = False
    strict_values: list[bool] = []
    for rule in status_rules:
        params = rule.get("parameters", {})
        configured = params.get("required_status_checks")
        if isinstance(configured, list):
            for item in configured:
                if isinstance(item, dict) and isinstance(item.get("context"), str):
                    contexts.add(item["context"])
                else:
                    status_unknown = True
        else:
            status_unknown = True
        strict = params.get("strict_required_status_checks_policy")
        if isinstance(strict, bool):
            strict_values.append(strict)
        else:
            status_unknown = True

    expected_contexts = set(requirement["requiredStatusChecks"])
    missing = expected_contexts - contexts
    if not missing:
        add_check(
            checks,
            prefix + "requiredStatusChecks",
            sorted(expected_contexts),
            sorted(contexts),
            comparator=lambda expected, actual: set(expected).issubset(set(actual)),
        )
    elif status_unknown or unknown_applicability:
        add_unknown(
            checks,
            prefix + "requiredStatusChecks",
            sorted(expected_contexts),
            f"cannot prove required contexts; observed={sorted(contexts)}",
        )
    else:
        add_check(
            checks,
            prefix + "requiredStatusChecks",
            sorted(expected_contexts),
            sorted(contexts),
            comparator=lambda expected, actual: set(expected).issubset(set(actual)),
        )

    strict_required = any(strict_values)
    if strict_required:
        add_check(checks, prefix + "requireUpToDate", requirement["requireUpToDate"], True)
    elif status_unknown or unknown_applicability:
        add_unknown(
            checks,
            prefix + "requireUpToDate",
            requirement["requireUpToDate"],
            "strict status-check policy cannot be proven",
        )
    else:
        add_check(checks, prefix + "requireUpToDate", requirement["requireUpToDate"], False)


def audit(
    target: dict[str, Any],
    repository: dict[str, Any],
    branch: dict[str, Any] | None,
    rulesets: list[dict[str, Any]] | None,
    *,
    branch_error: str | None = None,
    rulesets_error: str | None = None,
) -> list[dict[str, str]]:
    spec = target["spec"]
    checks: list[dict[str, str]] = []

    add_check(checks, "description", spec["description"], repository.get("description"))
    add_check(checks, "homepage", spec.get("homepage"), repository.get("homepage"))
    add_check(
        checks,
        "topics",
        spec.get("topics", []),
        repository.get("topics", []),
        comparator=lambda expected, actual: set(expected).issubset(set(actual or [])),
    )

    features = spec["features"]
    add_check(checks, "wiki", features["wiki"], repository.get("has_wiki"))
    add_check(checks, "discussions", features["discussions"], repository.get("has_discussions"))

    merge = spec["merge"]
    add_check(checks, "merge.squash", merge["squash"], repository.get("allow_squash_merge"))
    add_check(checks, "merge.mergeCommit", merge["mergeCommit"], repository.get("allow_merge_commit"))
    add_check(checks, "merge.rebase", merge["rebase"], repository.get("allow_rebase_merge"))
    add_check(checks, "merge.autoMerge", merge["autoMerge"], repository.get("allow_auto_merge"))
    add_check(checks, "merge.deleteBranchOnMerge", merge["deleteBranchOnMerge"], repository.get("delete_branch_on_merge"))
    add_check(checks, "merge.updateBranch", merge["updateBranch"], repository.get("allow_update_branch"))
    add_check(checks, "merge.squashPrTitleDefault", merge["squashPrTitleDefault"], repository.get("use_squash_pr_title_as_default"))

    default_branch = spec["defaultBranch"]
    add_check(checks, "defaultBranch.name", default_branch["name"], repository.get("default_branch"))
    if branch is None:
        add_unknown(checks, "defaultBranch.protected", default_branch["protected"], branch_error or "unavailable")
    else:
        add_check(checks, "defaultBranch.protected", default_branch["protected"], branch.get("protected"))

    audit_ruleset_semantics(
        checks,
        target,
        rulesets,
        default_branch["name"],
        rulesets_error,
    )
    return checks


def print_report(checks: list[dict[str, str]]) -> None:
    for check in checks:
        print(f"{check['status']:7} {check['name']}: expected={check['expected']} actual={check['actual']}")
    counts = {status: sum(item["status"] == status for item in checks) for status in ("PASS", "DRIFT", "UNKNOWN")}
    print(f"Repository settings audit: PASS={counts['PASS']} DRIFT={counts['DRIFT']} UNKNOWN={counts['UNKNOWN']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only audit of GitHub repository settings against DAT target state.")
    parser.add_argument("--target", default=str(DEFAULT_TARGET))
    parser.add_argument("--repository", help="owner/name; defaults to target metadata.repository")
    parser.add_argument("--strict", action="store_true", help="Return non-zero on DRIFT or UNKNOWN.")
    args = parser.parse_args()

    target = load_target(Path(args.target))
    repository_name = args.repository or target["metadata"]["repository"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository_name):
        raise SystemExit("--repository must use a valid owner/name form")

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    api = f"https://api.github.com/repos/{repository_name}"
    repository, repository_error = fetch_json(api, token)
    if repository is None:
        print(f"Repository settings audit failed: repository metadata unavailable ({repository_error})")
        return 2

    branch_name = target["spec"]["defaultBranch"]["name"]
    branch, branch_error = fetch_json(f"{api}/branches/{branch_name}", token)
    ruleset_summaries, rulesets_error = fetch_json(f"{api}/rulesets", token)

    rulesets = None
    if isinstance(ruleset_summaries, list):
        rulesets = []
        for summary in ruleset_summaries:
            ruleset_id = summary.get("id")
            if not isinstance(ruleset_id, int):
                rulesets.append(summary)
                continue
            detail, detail_error = fetch_json(f"{api}/rulesets/{ruleset_id}", token)
            if isinstance(detail, dict):
                rulesets.append(detail)
            else:
                unresolved = dict(summary)
                unresolved["_detail_error"] = detail_error or "unavailable"
                rulesets.append(unresolved)

    checks = audit(
        target,
        repository,
        branch if isinstance(branch, dict) else None,
        rulesets,
        branch_error=branch_error,
        rulesets_error=rulesets_error,
    )
    print_report(checks)

    if args.strict:
        if any(item["status"] == "DRIFT" for item in checks):
            return 1
        if any(item["status"] == "UNKNOWN" for item in checks):
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
