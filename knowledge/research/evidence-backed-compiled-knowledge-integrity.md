# Evidence-backed compiled knowledge integrity

## Status

**Research note / deferred knowledge-integrity evaluation candidate.**

This note does not change EXP-001, frozen artifacts, DAT schemas, canonical topologies, routing policies, Runtime Adapter behavior, or evaluation semantics. Any normative knowledge-admission contract or validator change is deferred until the EXP-001 Feature Freeze is completed.

Tracking: [Issue #63](https://github.com/s977043/dynamic-agent-topology/issues/63)

## Primary source

- Joon An: [LLM Wiki: Building a Personal Knowledge Base for Academic Papers with AI Agents](https://gist.github.com/joonan30/cbce305684d079dbe9a3fbaefe4e3959)
- Revised: 2026-08
- Upstream inspiration: [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/1dd0294ef9567971c1e4348a90d69285)
- Discovery pointer: [X post](https://x.com/rvaniaaaa/status/2107221534821498977)

The X post is a discovery pointer only. DAT treats the underlying operating report as the evidence source.

## Source claims

The operating report describes an LLM-maintained academic-paper wiki that had grown beyond 15,000 PDFs. At the reviewed revision it reports 15,259 PDFs, 14,872 source summaries, and 16,294 wiki pages.

It reports silent extraction failures even when extraction reports success, including:

- minus signs disappearing;
- table columns being reordered or merged;
- image-based tables remaining invisible to text extraction and missing-content checks;
- body sections silently disappearing for some font runs;
- figure reading order binding values to the wrong labels;
- superscripts being flattened;
- another paper being appended to a PDF and silently merged into one extracted document.

The source therefore records extraction provenance such as source format, extractor/version, and extraction date, and recommends re-reading the original PDF when a claim is sign-, figure-, or layout-sensitive.

The source also defines a **synthesis-orphan**: a source/wiki pair with no link into an overview or concept page. Each ingest is expected to connect into the synthesis layer, place the paper in context, and check whether it strengthens, narrows, contradicts, or replaces an existing claim.

These are operator-reported practices and observations from one knowledge-base implementation. They are not independently reproduced DAT benchmark results.

## DAT interpretation

The useful lesson is broader than a particular wiki layout:

~~~text
processed != correct
linked != verified
summary != source evidence
~~~

DAT should not infer semantic correctness from a successful extractor exit, generated summary, successful ingest pipeline, backlink, or internally consistent derived page.

The closest existing DAT concerns are:

- **Context** - source material and derived context can be missing, corrupted, stale, or disconnected;
- **Harness** - extraction / validation tooling can report success while the content is semantically wrong;
- **Evaluation** - completion criteria must distinguish process completion from evidence-backed acceptance;
- **Verification** - a Verifier needs source-grounded evidence and must not treat generated knowledge as its own proof.

This is not evidence for a new Knowledge Architecture Plane. A future solution should first attempt to compose existing Context, Harness, Evaluation, and Verification contracts.

## Candidate invariant: evidence-backed knowledge admission

A future persistent-knowledge workflow may need an explicit admission invariant:

~~~text
Source
  -> Extraction
  -> Derived claim
  -> Source provenance
  -> Synthesis / cross-reference
  -> Contradiction / supersede check
  -> Independent verification
  -> Admitted knowledge
~~~

Possible checks include:

~~~yaml
knowledge_admission:
  raw_source_preserved: true
  extraction_provenance_known: true
  claim_source_traceable: true
  synthesis_connected: true
  contradiction_check_completed: true
  independent_verification_passed: true
~~~

This is a **candidate evaluation shape**, not a current DAT schema.

A link-only rule is intentionally insufficient. Connectivity helps detect isolated knowledge, but it does not prove that either endpoint is correct.

## Why synthesis-orphan detection is still useful

The synthesis requirement addresses a different failure mode from factual verification. An isolated summary may be source-grounded yet operationally useless because it never affects an overview, concept, decision, contradiction record, or future retrieval path.

Orphan detection can therefore serve as a **coverage / integration signal**. It should not be promoted into a correctness signal.

## Hypotheses

### H1 - extraction provenance reduces silent acceptance

Preserving the raw source plus extractor identity/version and targeted source re-checks may reduce false acceptance of extraction corruption compared with treating successful extraction as complete.

### H2 - synthesis connectivity improves integration

Requiring persistent knowledge to connect into a synthesis / decision context may reduce isolated summaries and improve later reuse. This concerns integration, not truth.

### H3 - evidence-backed admission outperforms link-only completion

A gate combining provenance, claim-source traceability, contradiction checks, and independent verification may reduce false acceptance compared with a rule based only on successful processing plus graph connectivity.

### H4 - the abstraction may be unnecessary

Existing Context Boundary, Harness diagnostics, Evidence binding, and Verifier separation may be sufficient without introducing a new machine-readable knowledge contract. Rejecting the new abstraction is a valid result.

## Cheapest useful verification after EXP-001

Do not build a generic knowledge platform first.

1. Identify a concrete DAT knowledge/context use case or recurring failure.
2. Confirm whether existing Context / Harness / Evaluation contracts already express the needed invariant.
3. Prepare a small disposable corpus with known edge cases: sign-sensitive text, image-based table, multi-column layout, deliberately missing body section, and intentionally concatenated documents.
4. Keep raw sources immutable and record extractor/version provenance.
5. Compare:
   - baseline: process/extractor success is sufficient;
   - candidate A: provenance + deterministic extraction checks;
   - candidate B: A + synthesis-orphan detection;
   - candidate C: B + source-grounded independent verification.
6. Measure extraction fidelity, claim-source traceability, false acceptance, orphan rate, contradiction/supersede detection, human intervention, and operational cost.
7. Treat missing or ambiguous evidence as UNKNOWN / INCONCLUSIVE.
8. Adopt only the smallest intervention whose benefit is observable.

## Review and verification boundary

For persistent knowledge, review and verification should remain separate:

~~~text
Extractor / Compiler
        -> Reviewer: structure, clarity, synthesis quality
        -> Verifier: source-grounded claim checks
        -> Admission decision
~~~

This preserves Reviewer != Verifier, Verifier != Evidence, and Attestation != Verification. An LLM-generated summary or wiki page cannot verify itself merely by being internally coherent.

## Rejection / deferral evidence

Reject or defer an explicit knowledge-admission abstraction when:

- the repository does not have a persistent compiled-knowledge use case;
- existing Context / Harness / Evidence contracts are sufficient;
- orphan detection adds maintenance cost without improving downstream use;
- source-grounded checks cannot materially reduce false acceptance;
- most failures are better solved at ingestion/extraction;
- the proposal requires storage-specific wiki or graph concepts in DAT core;
- evidence is too sparse to justify stable semantics.

## What is retained during the freeze

During EXP-001, retain only these hypotheses:

- process success is not semantic correctness;
- persistent derived knowledge should retain traceability to source evidence;
- synthesis connectivity and correctness are separate properties;
- extraction provenance can matter when upstream tooling silently degrades content;
- independent Verification must not trust the generated knowledge artifact as its own evidence.

No new schema, knowledge graph, validator behavior, topology, runtime behavior, or EXP-001 evaluation semantics are adopted during the active freeze.

Accordingly, knowledge/sources.yaml records the operating report with adopted: [].

## Adoption gate

Revisit this note only after EXP-001 unfreeze conditions are satisfied. The first post-freeze review should start from an observed DAT knowledge/context need. If no such need exists, close Issue #63 without implementation.
