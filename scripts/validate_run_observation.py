#!/usr/bin/env python3
"""Validate RunObservation records (docs/RUN_OBSERVATION_DESIGN.md).

With paths, every file must pass. Without paths, the committed fixtures are
checked: fixtures/run-observation/valid/ must pass and
fixtures/run-observation/invalid/ must fail. Warnings (for example an
interrupted outcome without interruptionKind) are printed but do not fail.
"""
from datetime import datetime
from pathlib import Path
import json
import math
import re
import sys

from jsonschema import Draft202012Validator, FormatChecker
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "run-observation.schema.json"
FIXTURES = ROOT / "fixtures" / "run-observation"

MAX_STRING_LENGTH = 200
ABSOLUTE_PATH = re.compile(r"(/Users/|/home/|\b[A-Za-z]:\\)")
TOKEN_PREFIX = re.compile(r"(?<![A-Za-z0-9])(ghp_|gho_|ghu_|ghs_|ghr_|github_pat_|sk-)")
CANDIDATE_RUN = re.compile(r"[A-Za-z0-9+/=_-]{32,}")
MIN_ENTROPY_BITS = 4.0
WALL_CLOCK_TOLERANCE_MS = 60_000

VERIFIER_KIND_BY_REVIEWER = {
    "separate-session": "separate-session",
    "separate-model": "separate-model",
    "human": "human",
}

# reviews[].decision stays a free string so existing records remain valid;
# aggregation maps known aliases onto these canonical values.
DECISION_ALIASES = {
    "approve": "approve",
    "approved": "approve",
    "merge-ok": "approve",
    "changes-requested": "changes-requested",
    "changes-required": "changes-requested",
    "request-changes": "changes-requested",
    "comment": "comment",
    "comments": "comment",
    "unknown": "unknown",
}


def normalize_decision(value):
    return DECISION_ALIASES.get(value, "other")


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def construct_unique_mapping(loader, node, deep=False):
    keys = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            hash(key)
        except TypeError:
            raise yaml.constructor.ConstructorError(
                None, None, "mapping key must be a scalar", key_node.start_mark
            ) from None
        if key in keys:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key {key!r}", key_node.start_mark
            )
        keys.add(key)
    return loader.construct_mapping(node, deep=deep)


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_unique_mapping)


def load_record(path, validator):
    """Read one unambiguous YAML mapping and apply the shared record checks."""
    try:
        record = yaml.load(Path(path).read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        return None, [f"cannot read: {error}"]
    if not isinstance(record, dict):
        return None, ["record must be a mapping"]
    return record, validate_record(record, validator)



def shannon_entropy(text):
    counts = {}
    for char in text:
        counts[char] = counts.get(char, 0) + 1
    return -sum(n / len(text) * math.log2(n / len(text)) for n in counts.values())


def looks_high_entropy(run):
    has_classes = (
        any(c.islower() for c in run)
        and any(c.isupper() for c in run)
        and any(c.isdigit() for c in run)
    )
    return has_classes and shannon_entropy(run) >= MIN_ENTROPY_BITS


def iter_strings(value, location="$"):
    if isinstance(value, str):
        yield location, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from iter_strings(item, f"{location}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from iter_strings(item, f"{location}[{index}]")


def check_redaction(record):
    errors = []
    for location, text in iter_strings(record):
        if len(text) > MAX_STRING_LENGTH:
            errors.append(f"{location}: string longer than {MAX_STRING_LENGTH} characters")
        if ABSOLUTE_PATH.search(text):
            errors.append(f"{location}: contains an absolute path")
        if TOKEN_PREFIX.search(text):
            errors.append(f"{location}: contains a token-like prefix")
        elif any(looks_high_entropy(run) for run in CANDIDATE_RUN.findall(text)):
            errors.append(f"{location}: contains a long high-entropy string")
    reason = record.get("outcomeReason")
    if isinstance(reason, str) and ("\n" in reason or "\r" in reason):
        errors.append("$.outcomeReason: must be a single line")
    return errors


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def check_counts(record):
    errors = []
    started, ended, wall = record["startedAt"], record["endedAt"], record["wallClockMs"]
    if wall != "unknown" and "unknown" in (started, ended):
        errors.append("wallClockMs: requires both startedAt and endedAt to be known")
    if "unknown" not in (started, ended):
        elapsed_ms = (parse_time(ended) - parse_time(started)).total_seconds() * 1000
        if elapsed_ms < 0:
            errors.append("endedAt: earlier than startedAt")
        elif wall != "unknown" and abs(wall - elapsed_ms) > WALL_CLOCK_TOLERANCE_MS:
            errors.append("wallClockMs: does not match endedAt - startedAt")
    tasks = record["tasks"]
    if "unknown" not in (tasks["total"], tasks["delegated"]) and tasks["delegated"] > tasks["total"]:
        errors.append("tasks.delegated: greater than tasks.total")
    return errors


def root_review(reviews, artifacts):
    """Return the review that grounds verifierKind, or None.

    The last role: verifier review whose target is a merged artifact. When the
    wave merged nothing, the last role: verifier review of any target is used.
    """
    merged = {a["ref"] for a in artifacts if a["state"] == "merged"}
    verifiers = [r for r in reviews if r["role"] == "verifier"]
    if merged:
        verifiers = [r for r in verifiers if r["target"] in merged]
    return verifiers[-1] if verifiers else None


def check_basis(record):
    errors = []
    basis = record["topologyBasis"]
    reviews = record["reviews"]
    verification = basis["verification"]
    verifier_kind = basis.get("verifierKind")

    if verification == "yes" and verifier_kind is None:
        errors.append("topologyBasis.verifierKind: required when verification is yes")
    if verification != "yes" and verifier_kind is not None:
        errors.append("topologyBasis.verifierKind: allowed only when verification is yes")

    if reviews == "unknown":
        if verifier_kind not in (None, "organizer"):
            errors.append("topologyBasis.verifierKind: no grounding review (reviews is unknown)")
        if basis["independentReview"] != "unknown":
            errors.append("topologyBasis.independentReview: must be unknown when reviews is unknown")
        return errors

    root = root_review(reviews, record["artifacts"])
    if verifier_kind == "organizer" and root is not None:
        errors.append("topologyBasis.verifierKind: 'organizer' is allowed only without a grounding review")
    if verifier_kind not in (None, "organizer"):
        if root is None:
            errors.append("topologyBasis.verifierKind: no grounding role: verifier review")
        elif VERIFIER_KIND_BY_REVIEWER.get(root["reviewerKind"]) != verifier_kind:
            errors.append(
                f"topologyBasis.verifierKind: {verifier_kind!r} does not match grounding review "
                f"reviewerKind {root['reviewerKind']!r}"
            )
    if any(r["reviewerKind"] == "same-session" and r["role"] == "verifier" for r in reviews):
        errors.append("reviews: same-session review cannot have role verifier")
    if any(r["role"] == "verifier" for r in reviews) and verification != "yes":
        errors.append("topologyBasis.verification: must be yes when a role: verifier review exists")
    has_independent_advisory = any(
        r["role"] == "advisory" and r["reviewerKind"] in VERIFIER_KIND_BY_REVIEWER for r in reviews
    )
    if basis["independentReview"] == "yes" and not has_independent_advisory:
        errors.append(
            "topologyBasis.independentReview: 'yes' requires a role: advisory review by "
            "separate-session, separate-model, or human"
        )
    elif basis["independentReview"] != ("yes" if has_independent_advisory else "no"):
        errors.append("topologyBasis.independentReview: does not match independent role: advisory reviews")
    return errors


def record_warnings(record):
    """Return non-blocking findings for a record that already passed validation."""
    warnings = []
    if record["outcome"] == "interrupted" and "interruptionKind" not in record:
        warnings.append("interruptionKind: missing for an interrupted outcome")
    if record["reviews"] != "unknown":
        for index, review in enumerate(record["reviews"]):
            if normalize_decision(review["decision"]) == "other":
                warnings.append(f"reviews[{index}].decision: {review['decision']!r} is not a known decision")
    return warnings


def allowed_topologies(basis):
    """Topologies permitted by the decision table in design section 5.2.

    The basis cannot tell P0 from human-only work, nor whether a Worker
    existed when nothing was delegated, so `other` stays allowed there.
    """
    agent, delegated, verification = basis["agentInvolved"], basis["delegated"], basis["verification"]
    review, specialist = basis["independentReview"], basis["specialistRole"]
    kind = basis.get("verifierKind")
    if "unknown" in (agent, delegated, verification):
        return {"unknown"}
    if agent == "no":
        return {"P0", "other"}
    extra = {"other"} if delegated == "no" else set()
    if verification == "no" or (delegated == "no" and kind == "organizer"):
        return {"T0"} | extra
    if delegated == "yes":
        if review == "unknown" or (review == "yes" and specialist == "unknown"):
            return {"unknown"}
        if review == "yes":
            return {"T3"} if specialist == "yes" else {"T2"}
        return {"T1"}
    if kind in VERIFIER_KIND_BY_REVIEWER:
        return {"T1"} | extra
    return {"unknown"} | extra


def validate_record(record, validator):
    schema_errors = sorted(validator.iter_errors(record), key=lambda e: list(e.absolute_path))
    if schema_errors:
        return [
            f"schema: {'/'.join(str(p) for p in error.absolute_path) or '$'}: {error.message}"
            for error in schema_errors
        ]
    errors = check_redaction(record) + check_counts(record)
    basis_errors = check_basis(record)
    errors += basis_errors
    if not basis_errors:
        allowed = allowed_topologies(record["topologyBasis"])
        if record["topologyEquivalent"] not in allowed:
            errors.append(
                f"topologyEquivalent: {record['topologyEquivalent']!r} does not follow from "
                f"topologyBasis (expected one of {sorted(allowed)})"
            )
    return errors


def load_validator():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate_file(path, validator):
    _, errors = load_record(path, validator)
    return errors


def main(argv):
    validator = load_validator()
    failed = False
    if argv:
        for path in argv:
            record, errors = load_record(path, validator)
            for error in errors:
                print(f"{path}: {error}")
            if record is not None and not errors:
                for warning in record_warnings(record):
                    print(f"{path}: warning: {warning}")
            failed = failed or bool(errors)
        if failed:
            return 1
        print(f"RunObservation validation passed: {len(argv)} file(s).")
        return 0

    valid = sorted((FIXTURES / "valid").glob("*.yaml"))
    invalid = sorted((FIXTURES / "invalid").glob("*.yaml"))
    if not valid or not invalid:
        print("RunObservation fixtures are missing")
        return 1
    for path in valid:
        for error in validate_file(path, validator):
            print(f"{path.relative_to(ROOT)}: {error}")
            failed = True
    for path in invalid:
        if not validate_file(path, validator):
            print(f"{path.relative_to(ROOT)}: invalid fixture was accepted")
            failed = True
    if failed:
        return 1
    print(f"RunObservation validation passed: {len(valid)} valid, {len(invalid)} invalid fixture(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
