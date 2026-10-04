#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
import sys
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

    def unresolved_pattern(value: Any) -> bool:
        if not isinstance(value, str):
            return True
        if value.startswith("~"):
            return value not in {"~ALL", "~DEFAULT_BRANCH"}
        return any(char in value for char in "*?[")

    unknown_exclude = any(unresolved_pattern(item) for item in excludes)
    if any(item in matching_tokens for item in includes):
        return None if unknown_exclude else True

    if not includes:
        return False

    if all(isinstance(item, str) and not unresolved_pattern(item) for item in includes):
        return False

    return None


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
    add_check(
        checks,
        "merge.deleteBranchOnMerge",
        merge["deleteBranchOnMerge"],
        repository.get("delete_branch_on_merge"),
    )
    add_check(checks, "merge.updateBranch", merge["updateBranch"], repository.get("allow_update_branch"))
    add_check(
        checks,
        "merge.squashPrTitleDefault",
        merge["squashPrTitleDefault"],
        repository.get("use_squash_pr_title_as_default"),
    )

    default_branch = spec["defaultBranch"]
    add_check(checks, "defaultBranch.name", default_branch["name"], repository.get("default_branch"))
    if branch is None:
        add_unknown(checks, "defaultBranch.protected", default_branch["protected"], branch_error or "unavailable")
    else:
        add_check(checks, "defaultBranch.protected", default_branch["protected"], branch.get("protected"))

    if rulesets is None:
        add_unknown(
            checks,
            "defaultBranch.activeRulesetRequired",
            default_branch["activeRulesetRequired"],
            rulesets_error or "unavailable",
        )
    else:
        active_branch_rulesets = [
            item for item in rulesets
            if item.get("target") == "branch" and item.get("enforcement") == "active"
        ]
        applicability = [
            ruleset_targets_default_branch(item, default_branch["name"])
            for item in active_branch_rulesets
        ]
        if any(value is True for value in applicability):
            add_check(
                checks,
                "defaultBranch.activeRulesetRequired",
                default_branch["activeRulesetRequired"],
                True,
            )
        elif any(value is None for value in applicability):
            add_unknown(
                checks,
                "defaultBranch.activeRulesetRequired",
                default_branch["activeRulesetRequired"],
                "active branch ruleset exists but default-branch applicability is not provable",
            )
        else:
            add_check(
                checks,
                "defaultBranch.activeRulesetRequired",
                default_branch["activeRulesetRequired"],
                False,
            )

    return checks


def print_report(checks: list[dict[str, str]]) -> None:
    for check in checks:
        print(
            f"{check['status']:7} {check['name']}: "
            f"expected={check['expected']} actual={check['actual']}"
        )
    counts = {status: sum(item["status"] == status for item in checks) for status in ("PASS", "DRIFT", "UNKNOWN")}
    print(
        "Repository settings audit: "
        f"PASS={counts['PASS']} DRIFT={counts['DRIFT']} UNKNOWN={counts['UNKNOWN']}"
    )


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
