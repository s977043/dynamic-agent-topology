#!/usr/bin/env python3
"""Disposable #63 known-source probe; optional libraries, no runtime integration."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(text):
    return ' '.join(text.split())


def facts(text, required, forbidden, available):
    if not available or not text.strip():
        return 'UNKNOWN'
    if any(norm(x) in norm(text) for x in forbidden):
        return 'FAIL'
    if any(norm(x) not in norm(text) for x in required):
        return 'UNKNOWN'
    return 'PASS'


def gate(evidence, requirements):
    """Receives evidence only; no case identifier or expected truth."""
    factual = facts(evidence['text'], requirements['required'], requirements['forbidden'], evidence['available'])
    provenance = ('UNKNOWN' if not evidence['source_hash'] or not evidence['extractor'] else
                  'PASS' if evidence['source_hash'] == requirements['source_hash'] else 'FAIL')
    freshness = ('UNKNOWN' if evidence['revision'] is None else
                 'PASS' if evidence['revision'] == requirements['revision'] else 'FAIL')
    connectivity = 'PASS' if evidence['connected'] else 'FAIL'
    checks = dict(factual=factual, provenance=provenance, freshness=freshness, connectivity=connectivity)
    checks['admission'] = 'FAIL' if 'FAIL' in checks.values() else 'UNKNOWN' if 'UNKNOWN' in checks.values() else 'PASS'
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=False)  # Refuse overwrite before any output.
    start = time.monotonic()
    commands = []

    def save(name, obj):
        (out / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')

    def command(argv):
        before = time.monotonic()
        try:
            p = subprocess.run(argv, capture_output=True, text=True, check=False)
            record = dict(argv=argv, exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr)
        except OSError as exc:
            record = dict(argv=argv, exit_code=None, stdout='', stderr=str(exc))
        record['seconds'] = time.monotonic() - before
        commands.append(record)
        return record

    versions = dict(python=sys.version, platform=platform.platform())
    for lib in ['reportlab', 'Pillow', 'pypdf', 'PyMuPDF']:
        try:
            versions[lib] = importlib.metadata.version(lib)
        except importlib.metadata.PackageNotFoundError:
            versions[lib] = None
    versions['pdftotext'] = command(['pdftotext', '-v'])
    save('versions.json', versions)
    repo = Path(__file__).resolve().parents[2]
    save('preregistration.json', dict(plan_sha256=sha(repo / 'docs/CLOUD_VERIFICATION_PLAN.md'), script_sha256=sha(Path(__file__))))
    # Optional source-generation dependencies are required for this disposable run.
    from reportlab.pdfgen import canvas
    from PIL import Image, ImageDraw
    import fitz

    required = {
        'signed': ['Net change: -12 units', 'Required section: safety margin 7 units'],
        'image': ['Treatment A: -12', 'Treatment B: 7'],
        'columns': ['Left result: -12 units', 'Right result: 7 units'],
        'foreign': ['FOREIGN PAPER: unrelated result 99'],
    }
    signed_excludes = required['foreign'] + ['Net change: 12 units']
    # Freeze the case oracle before any extraction, independently of measured output.
    save('oracle.json', dict(required=required, signed_excludes=signed_excludes,
        truth_correct=['signed-linked', 'signed-orphan', 'image-linked', 'columns-linked', 'missing-provenance', 'unknown-revision', 'stale-hash'],
        truth_incorrect=['lost-minus', 'missing-section', 'concat'],
        text_truth={'current': 'correct', 'stale': 'incorrect', 'missing-revision': 'correct'},
        unavailable_claim_truth='UNKNOWN'))
    for source, lines in required.items():
        pdf = out / f'{source}.pdf'
        c = canvas.Canvas(str(pdf), invariant=1, pagesize=(612, 792))
        if source == 'image':
            im = Image.new('RGB', (1000, 260), 'white')
            draw = ImageDraw.Draw(im)
            # Pillow's bundled default font is local; enlarge by nearest-neighbor.
            small = Image.new('RGB', (250, 65), 'white')
            d = ImageDraw.Draw(small)
            d.text((10, 10), lines[0], fill='black')
            d.text((10, 35), lines[1], fill='black')
            im = small.resize((1000, 260))
            im.save(out / 'image-table.png')
            c.drawImage(str(out / 'image-table.png'), 40, 500, width=500, height=130)
        elif source == 'columns':
            c.drawString(35, 740, lines[0])
            c.drawString(320, 740, lines[1])
        else:
            for i, line in enumerate(lines):
                c.drawString(40, 740 - 30 * i, line)
        c.showPage()
        c.save()
        pdf.chmod(0o444)
    hashes = {s: sha(out / f'{s}.pdf') for s in required}
    doc = fitz.open(out / 'image.pdf')
    doc[0].get_pixmap().save(out / 'image-render.png')
    doc.close()
    save('sources.json', dict(hashes_before=hashes, image_visual_review='PENDING; source image must be independently inspected'))
    extracted = {}
    for engine in ['pypdf', 'pdftotext']:
        for source in required:
            pdf = out / f'{source}.pdf'
            if engine == 'pypdf':
                record = command([sys.executable, '-c', 'import sys; from pypdf import PdfReader; print("\\n".join(p.extract_text() or "" for p in PdfReader(sys.argv[1]).pages))', str(pdf)])
            else:
                record = command(['pdftotext', str(pdf), '-'])
            (out / f'{source}-{engine}.txt').write_text(record['stdout'])
            extracted[engine, source] = record
    rows = []
    details = []

    def observe(case, stratum, engine, evidence, req, truth, process):
        checks = gate(evidence, req)
        row = dict(case=case, stratum=stratum, engine=engine, truth=truth,
                   baseline_process='PASS' if process else 'UNKNOWN',
                   baseline_link='PASS' if process and evidence['connected'] and evidence['source_hash'] else 'FAIL' if process else 'UNKNOWN', **checks)
        rows.append(row)
        details.append(dict(report=row, evidence=evidence, requirements=req))

    for engine in ['pypdf', 'pdftotext']:
        for case in ['signed-linked', 'signed-orphan', 'image-linked', 'columns-linked', 'missing-provenance', 'unknown-revision', 'lost-minus', 'missing-section', 'concat', 'stale-hash']:
            source = 'image' if case == 'image-linked' else 'columns' if case == 'columns-linked' else 'signed'
            rec = extracted[engine, source]
            text = rec['stdout']
            available = rec['exit_code'] == 0
            # Require real source facts before mutation; missing extraction cannot fabricate a case.
            precondition = facts(text, required[source], [], available) == 'PASS'
            injected = case in ['lost-minus', 'missing-section', 'concat', 'stale-hash']
            if injected:
                available = available and precondition
                if available and case == 'lost-minus':
                    text = text.replace('-12', '12')
                elif available and case == 'missing-section':
                    text = text.replace(required[source][1], '')
                elif available and case == 'concat':
                    foreign = extracted[engine, 'foreign']
                    available = facts(foreign['stdout'], required['foreign'], [], foreign['exit_code'] == 0) == 'PASS'
                    if available:
                        text += '\n' + foreign['stdout']
            evidence = dict(text=text, available=available, source_hash=None if case == 'missing-provenance' else 'stale' if case == 'stale-hash' else hashes[source], extractor=engine, revision=None if case == 'unknown-revision' else 'r1', connected=case != 'signed-orphan')
            req = dict(required=required[source], forbidden=signed_excludes if source == 'signed' else [], source_hash=hashes[source], revision='r1')
            # Independent corpus scoring happens after evidence construction. A real
            # nonempty extraction mismatch remains incorrect, never discarded.
            if not available or not text.strip():
                truth = 'UNKNOWN'
            elif injected:
                truth = 'incorrect' if case in ['lost-minus', 'missing-section', 'concat'] else 'correct'
            else:
                truth = 'PENDING_REVIEW'
            observe(case, 'injected' if injected else 'extraction', engine, evidence, req, truth, rec['exit_code'] == 0)
    canonical = 'freeze status completed; revision 3'
    canonical_path = out / 'canonical-context.txt'
    canonical_path.write_text(canonical + '\n')
    canonical_path.chmod(0o444)
    revision = '3b760ffc56bd724d6378abaff1a46e7036365fab'
    save('superseded.json', dict(source_revision=revision, supersedes='prior-active-checkpoint', relation='completed supersedes active', synthetic_mirror_of_issue=15))
    for case in ['current', 'stale', 'missing-revision']:
        evidence = dict(text=canonical if case != 'stale' else 'freeze status active; revision 3', available=True, source_hash=sha(canonical_path), extractor='text-context', revision=revision if case == 'current' else None if case == 'missing-revision' else 'prior-active-checkpoint', connected=True)
        req = dict(required=[canonical], forbidden=['freeze status active'], source_hash=sha(canonical_path), revision=revision)
        observe(case, 'freshness-text', 'text-context', evidence, req, 'incorrect' if case == 'stale' else 'correct', True)
    after = {s: sha(out / f'{s}.pdf') for s in required}
    save('source-integrity.json', dict(before=hashes, after=after, unchanged=hashes == after))
    save('commands.json', commands)
    save('observations.json', details)
    with (out / 'observations.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    metrics = {}
    for stratum in ['extraction', 'injected', 'freshness-text']:
        subset = [r for r in rows if r['stratum'] == stratum]
        summary = dict(n=len(subset), truth_unknown=sum(r['truth'] == 'UNKNOWN' for r in subset), truth_pending_review=sum(r['truth'] == 'PENDING_REVIEW' for r in subset))
        for method in ['baseline_process', 'baseline_link', 'factual', 'admission']:
            bad = [r for r in subset if r['truth'] == 'incorrect']
            good = [r for r in subset if r['truth'] == 'correct']
            unknown = [r for r in subset if r['truth'] == 'UNKNOWN']
            summary[method] = dict(incorrect_denominator=len(bad), false_accept=sum(r[method] == 'PASS' for r in bad), correct_denominator=len(good), correct_hold_FAIL=sum(r[method] == 'FAIL' for r in good), correct_hold_UNKNOWN=sum(r[method] == 'UNKNOWN' for r in good), unsafe_admit_unknown=sum(r[method] == 'PASS' for r in unknown))
        metrics[stratum] = summary
    metrics['resources'] = dict(seconds=time.monotonic() - start, bytes_before_summary=sum(p.stat().st_size for p in out.iterdir() if p.is_file()), model_runs=0, monetary_cost='not measured', human_review_time='not measured')
    metrics['truth_status'] = 'Actual extraction truth requires independent raw-source/output review; initial metrics incomplete'
    save('summary.json', metrics)
    print(json.dumps(dict(output=str(out), observations=len(rows), source_hashes_unchanged=hashes == after)))
    return 0 if hashes == after else 1


if __name__ == '__main__':
    raise SystemExit(main())
