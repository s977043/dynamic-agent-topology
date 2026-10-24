#!/usr/bin/env python3
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_observation.py"
FIXTURES = ROOT / "fixtures" / "run-observation"

failures = []


def run(*args, env=None, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        cwd=cwd,
    )


def variant(source, workdir, observation_id, project):
    record = yaml.safe_load((FIXTURES / "valid" / source).read_text(encoding="utf-8"))
    record["metadata"]["observationId"] = observation_id
    record["metadata"]["project"] = project
    path = workdir / f"{len(list(workdir.iterdir()))}.yaml"
    path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
    return path


def expect(result, code, text, label):
    if result.returncode != code or text not in result.stdout:
        failures.append(f"{label}: expected exit {code} with {text!r}, got {result.returncode}\n{result.stdout}")


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    store = tmp / "store"
    work = tmp / "work"
    work.mkdir()

    first = FIXTURES / "valid" / "t1-separate-session-verifier.yaml"
    result = run("save", str(first), "--store", str(store))
    expect(result, 0, "OK obs-0001", "save valid record")
    if not (store / "project-a" / "obs-0001.yaml").is_file():
        failures.append("save must write <store>/<project>/<observationId>.yaml")

    expect(run("save", str(first), "--store", str(store)), 1, "already recorded", "duplicate observationId")

    unknown = variant("interrupted-no-merge-unknown-values.yaml", work, "obs-0002", "project-a")
    result = run("save", str(unknown), "--store", str(store))
    expect(result, 0, "rework.count", "save reports unknown fields")

    invalid = FIXTURES / "invalid" / "redaction-absolute-path-users.yaml"
    result = run("save", str(invalid), "--store", str(store))
    expect(result, 1, "NG", "invalid record")
    if any(store.glob("*/redaction*")) or len(list(store.glob("*/*.yaml"))) != 2:
        failures.append("invalid record must not be stored")

    expect(run("save", str(first), "--store", str(ROOT / "tmp-store")), 2, "outside the DAT repository", "store inside repo")
    if (ROOT / "tmp-store").exists():
        failures.append("refused store must not be created")

    repo = tmp / "adopter"
    (repo / ".git").mkdir(parents=True)
    expect(run("save", str(first), "--store", str(repo / "obs")), 2, "outside any git working tree", "store inside git tree")
    if (repo / "obs").exists():
        failures.append("store inside a git working tree must not be created")

    nested_store = tmp / "nested-git-store"
    nested_repo = nested_store / "nested-repo"
    nested_repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(nested_repo)], check=True)
    subprocess.run(
        ["git", "-C", str(nested_repo), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
         "commit", "-q", "--allow-empty", "-m", "fixture"],
        check=True,
    )
    nested_worktree = nested_store / "nested-worktree"
    subprocess.run(
        ["git", "-C", str(nested_repo), "worktree", "add", "-q", "--detach", str(nested_worktree), "HEAD"],
        check=True,
    )
    if not (nested_worktree / ".git").is_file():
        failures.append("linked-worktree regression must exercise a .git file")
    (nested_store / "linked-repo").symlink_to(nested_repo, target_is_directory=True)
    for project in ("nested-repo", "nested-worktree", "linked-repo"):
        record = variant("t1-separate-session-verifier.yaml", work, "obs-0110", project)
        result = run("save", str(record), "--store", str(nested_store))
        expect(result, 1, "outside any git working tree", f"destination inside {project}")
        if (nested_store / project / "obs-0110.yaml").exists():
            failures.append(f"git destination {project} must not receive an observation")
    if list(nested_store.glob("*/*.yaml")):
        failures.append("refused git destinations must not save observation records")

    for project, observation_id in (("../outside", "obs-0101"), ("a/b", "obs-0102"), ("project-a", "../obs-0103"), ("..", "obs-0104")):
        escape = variant("t1-separate-session-verifier.yaml", work, observation_id, project)
        expect(run("save", str(escape), "--store", str(store)), 1, "must match", f"path element {project}/{observation_id}")
    if (tmp / "outside").exists() or (store / "a").exists():
        failures.append("path escape must not create directories")

    outside = tmp / "outside-link-target"
    outside.mkdir()
    (store / "linked").symlink_to(outside, target_is_directory=True)
    linked = variant("t1-separate-session-verifier.yaml", work, "obs-0105", "linked")
    expect(run("save", str(linked), "--store", str(store)), 1, "outside the store", "symlinked project directory")
    if any(outside.iterdir()):
        failures.append("symlinked project directory must not receive a record")
    (store / "linked").unlink()

    duplicate = work / "duplicate.yaml"
    duplicate.write_text(
        first.read_text(encoding="utf-8") + "outcomeReason: ok\noutcomeReason: " + "gh" + "p_" + "EXAMPLE\n",
        encoding="utf-8",
    )
    expect(run("save", str(duplicate), "--store", str(store)), 1, "duplicate key", "duplicate key")
    if any("EXAMPLE" in p.read_text(encoding="utf-8") for p in store.glob("*/*.yaml")):
        failures.append("duplicate key record must not be stored")

    complex_key = work / "complex-key.yaml"
    complex_key.write_text(first.read_text(encoding="utf-8") + "? [a, b]\n: value\n", encoding="utf-8")
    expect(run("save", str(complex_key), "--store", str(store)), 1, "mapping key must be a scalar", "non-scalar key")

    broken = work / "broken.yaml"
    broken.write_text("metadata: [unclosed\n", encoding="utf-8")
    expect(run("save", str(broken), "--store", str(store)), 1, "cannot read", "malformed YAML")

    invalid_utf8 = work / "invalid-utf8.yaml"
    invalid_utf8.write_bytes(b"\xff\xfe")
    utf8_save_store = tmp / "utf8-save-store"
    result = run("save", str(invalid_utf8), "--store", str(utf8_save_store))
    expect(result, 1, "cannot read", "invalid UTF-8 save")
    if "Traceback" in result.stdout or utf8_save_store.exists():
        failures.append("invalid UTF-8 save must be refused without traceback or creating a store")

    utf8_sum_store = tmp / "utf8-sum-store"
    utf8_project = utf8_sum_store / "project-a"
    utf8_project.mkdir(parents=True)
    shutil.copyfile(first, utf8_project / "valid.yaml")
    shutil.copyfile(invalid_utf8, utf8_project / "invalid-utf8.yaml")
    result = run("sum", "--store", str(utf8_sum_store))
    for text in ("skipped invalid: project-a/invalid-utf8.yaml: cannot read", "observations: 1", "| project-a | T1 | 1 |"):
        expect(result, 1, text, "sum skips invalid UTF-8 and counts valid record")
    if "Traceback" in result.stdout:
        failures.append("invalid UTF-8 sum must skip the file without traceback")

    relative = variant("t1-separate-session-verifier.yaml", work, "obs-0106", "project-c")
    expect(run("save", str(relative), "--store", "rel-store", cwd=tmp), 0, "OK obs-0106", "relative store")
    if not (tmp / "rel-store" / "project-c" / "obs-0106.yaml").is_file():
        failures.append("relative store must resolve against the working directory")

    expect(run("sum", "--store", str(tmp / "missing")), 2, "store does not exist", "missing store directory")

    env = {k: v for k, v in os.environ.items() if k != "DAT_OBSERVATION_STORE"}
    expect(run("sum", env=env), 2, "DAT_OBSERVATION_STORE", "missing store")

    other = variant("t0-no-delegation-advisory-only.yaml", work, "obs-0003", "project-b")
    env["DAT_OBSERVATION_STORE"] = str(store)
    expect(run("save", str(other), env=env), 0, "OK obs-0003", "store from environment")

    cross = variant("t1-separate-session-verifier.yaml", work, "obs-0001", "project-z")
    expect(run("save", str(cross), "--store", str(store)), 1, "already recorded", "observationId in another project")
    if (store / "project-z").exists():
        failures.append("observationId recorded in another project must not be saved again")

    nested = store / "project-a" / "nested" / "obs-0301.yaml"
    nested.parent.mkdir()
    shutil.copyfile(first, nested)
    shutil.copyfile(first, store / "top-level.yaml")
    result = run("sum", "--store", str(store))
    for text in (
        "warning: not counted (outside <project>/<observationId>.yaml): project-a/nested/obs-0301.yaml",
        "warning: not counted (outside <project>/<observationId>.yaml): top-level.yaml",
        "observations: 3",
        "| approve | 1 |",
        "| changes-requested | 1 |",
        "| comment | 1 |",
        "endedAt unknown (cannot be placed in a period): 1",
    ):
        expect(result, 0, text, "sum warns about files outside the counted layout")
    shutil.rmtree(nested.parent)
    (store / "top-level.yaml").unlink()

    nested_id = variant("t0-no-delegation-advisory-only.yaml", work, "obs-0302", "project-b")
    (store / "project-b" / "deep").mkdir()
    shutil.copyfile(nested_id, store / "project-b" / "deep" / "obs-0302.yaml")
    expect(run("save", str(nested_id), "--store", str(store)), 1, "already recorded", "observationId in a nested file")
    shutil.rmtree(store / "project-b" / "deep")

    renamed = store / "project-b" / "renamed.yaml"
    renamed.write_text(variant("t0-no-delegation-advisory-only.yaml", work, "obs-0303", "project-b").read_text(encoding="utf-8"), encoding="utf-8")
    same_id = variant("t0-no-delegation-advisory-only.yaml", work, "obs-0303", "project-b")
    expect(run("save", str(same_id), "--store", str(store)), 1, "already recorded", "observationId stored under another file name")
    if (store / "project-b" / "obs-0303.yaml").exists():
        failures.append("observationId stored under another file name must not be saved again")
    shutil.copyfile(renamed, store / "project-a" / "copy.yaml")
    result = run("sum", "--store", str(store))
    expect(result, 1, "duplicate observationId obs-0303: project-a/copy.yaml, project-b/renamed.yaml", "sum detects duplicate observationId")
    if "observations:" in result.stdout:
        failures.append("sum must not print counts when observationIds are duplicated")
    (store / "project-a" / "copy.yaml").unlink()
    renamed.unlink()

    shutil.copyfile(invalid, store / "project-a" / "obs-bad.yaml")
    shutil.copyfile(complex_key, store / "project-a" / "obs-complex.yaml")
    piped = store / "pipe" / "obs-0201.yaml"
    piped.parent.mkdir()
    piped.write_text(variant("t0-no-delegation-advisory-only.yaml", work, "obs-0201", "a|b").read_text(encoding="utf-8"), encoding="utf-8")
    result = run("sum", "--store", str(store))
    for text in (
        "observations: 4",
        "| a\\|b | T0 | 1 |",
        "skipped invalid: project-a/obs-bad.yaml",
        "skipped invalid: project-a/obs-complex.yaml",
        "| project-a | T1 | 2 |",
        "| project-b | T0 | 1 |",
        "| T1 | completed | 1 |",
        "| T1 | interrupted | 1 |",
        "| T1 | 1/2 | 0 |",
        "| T0 | 2/2 | 0 |",
        "not evidence that a topology is better",
    ):
        expect(result, 1, text, "sum output with a skipped file")
    (store / "project-a" / "obs-bad.yaml").unlink()
    (store / "project-a" / "obs-complex.yaml").unlink()
    expect(run("sum", "--store", str(store)), 0, "observations: 4", "sum without invalid files")

if failures:
    print("RunObservation CLI tests failed:")
    for failure in failures:
        print(f"- {failure}")
    sys.exit(1)

print("RunObservation CLI tests passed.")
