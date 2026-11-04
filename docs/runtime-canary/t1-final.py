def select_latest(records):
    latest = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        record_id = record.get('id')
        revision = record.get('revision')
        if not isinstance(record_id, str) or not record_id:
            continue
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
            continue
        if record_id not in latest or revision > latest[record_id]['revision']:
            latest[record_id] = record
    return list(latest.values())
