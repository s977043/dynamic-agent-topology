def select_latest(records):
    latest = {}
    for record in records:
        latest[record['id']] = record
    return list(latest.values())
