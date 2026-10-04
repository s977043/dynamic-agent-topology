# Contributing

Thanks for contributing to Dynamic Agent Topology (DAT).

DAT is evidence-driven. Contributions should distinguish:

1. external source claims;
2. observed repository or runtime evidence;
3. DAT interpretation;
4. implementation or governance decisions.

Do not present an untested topology choice as a universal best practice.

## Before you start

- Search existing issues and pull requests first.
- For a bug, use the Bug report issue form and provide a minimal reproduction.
- For a design or behavior change, use the Proposal issue form and start from the problem, hypothesis, and evidence.
- If external research or a benchmark materially motivates the change, use the Research or design proposal form and separate the source claim from DAT interpretation.
- For usage or adoption help, use the Usage or adoption question form rather than forcing the request into a bug or proposal.
- For security-sensitive findings, follow [SECURITY.md](SECURITY.md) instead of opening a public issue.
- Check the active experiment freeze before touching experiment inputs, evaluation semantics, prompts, roles, scenarios, fixtures, or frozen validators.

Large or architectural changes should be discussed in an issue before implementation.

## Development setup

DAT currently uses Python 3.12 in CI.

Install the CI validation dependencies:

```bash
python -m pip install -r requirements-ci.txt
```

Run the same core validation used by CI by executing the relevant commands from [spec-lint.yml](.github/workflows/spec-lint.yml). At minimum, changes should keep the schema, semantic, experiment, pilot, and freeze validations green.

## Pull requests

Keep pull requests small enough to review. Use the pull request template and include:

- the problem or maintenance reason;
- explicit in-scope and out-of-scope boundaries;
- exact validation commands and results;
- compatibility or experiment impact;
- evidence supporting behavioral changes.

For topology, routing, role, verifier, or experiment-method changes, include the hypothesis and how the change can be evaluated or falsified.

For research-derived changes, explicitly separate:

- the source claim;
- DAT interpretation;
- what is proposed for evaluation;
- what evidence would reject, simplify, or defer the proposal.

A source citation is not evidence that a DAT design is effective.

## Generated and empirical artifacts

Do not fabricate missing evidence or fill unknown values with guesses. Failed, aborted, and inconclusive runs must remain distinguishable from successful runs.

Do not commit secrets, private source code, confidential prompts, or unsanitized execution traces.

## Releases

A version advertised in `README.md`, `README_en.md`, or `CITATION.cff` should correspond to an immutable Git tag and a GitHub Release.

Before publishing a release:

1. verify the intended release commit and confirm CI, CodeQL, and Scorecard are green on the relevant `main` revision;
2. update versioned documentation and `CITATION.cff` in the release PR;
3. merge the release PR;
4. create an immutable `vX.Y.Z` tag at the verified release commit; sign or annotate it when the release process supports that reliably;
5. publish a GitHub Release from that tag with concise user-facing notes;
6. verify that README status and citation metadata match the published tag.

Do not move an existing version tag to a newer commit. Publish a new patch or minor version instead.

## Review principles

Review should separate correctness, judgment, and verification:

- deterministic evidence outranks agent self-assessment;
- reviewer approval is not a substitute for executable validation;
- candidate generation is not evidence that a candidate is better;
- changes to authority or permissions require explicit scrutiny.

By participating in this project, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
