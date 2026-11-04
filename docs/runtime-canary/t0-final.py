def select_latest(records):
    latest = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        identifier = record.get('id')
        revision = record.get('revision')
        if not isinstance(identifier, str) or not identifier:
            continue
        if (not isinstance(revision, int)
                or isinstance(revision, bool)
                or revision < 0):
            continue
        if identifier not in latest or revision > latest[identifier]['revision']:
            latest[identifier] = record
    return list(latest.values())
