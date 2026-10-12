"""Durable reservation before a single HTTP request. Repeated keys never request again."""
import argparse, hashlib, json, os, time, urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parent
def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()
def attempt(key, url, dest, timeout=45):
    ledger = ROOT / 'attempts'
    ledger.mkdir(exist_ok=True)
    ident = hashlib.sha256(key.encode()).hexdigest()
    reservation = ledger / (ident + '.json')
    record = {'key': key, 'url': url, 'attempt_count': 1, 'status': 'RESERVED', 'started_at': now()}
    try:
        fd = os.open(reservation, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return {'key': key, 'status': 'ALREADY_ATTEMPTED_NO_RETRY', 'ledger': str(reservation)}
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2); f.flush(); os.fsync(f.fileno())
    dest = Path(dest).resolve()
    if ROOT not in dest.parents:
        record.update(status='SKIPPED', error='Destination must be inside automation workspace')
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        partial = dest.with_name(dest.name + '.partial')
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'V161-Research-Once/1.0'})
            deadline = time.monotonic() + 180
            with urllib.request.urlopen(request, timeout=timeout) as response, partial.open('xb') as f:
                record['final_url'] = response.url
                record['content_type'] = response.headers.get('Content-Type')
                while True:
                    if time.monotonic() > deadline: raise TimeoutError('Total download time limit exceeded')
                    block = response.read(1024 * 1024)
                    if not block: break
                    f.write(block)
            if not partial.stat().st_size: raise ValueError('Empty response')
            os.replace(partial, dest)
            record.update(status='DOWNLOADED_UNVALIDATED', size_bytes=dest.stat().st_size,
                          sha256=hashlib.sha256(dest.read_bytes()).hexdigest(), file=str(dest))
        except Exception as exc:
            record.update(status='SKIPPED', error=f'{type(exc).__name__}: {exc}')
    record['finished_at'] = now()
    temp = reservation.with_suffix('.tmp')
    temp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temp, reservation)
    with (ROOT / 'logs' / 'download_attempts.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
    return record
if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--key',required=True); p.add_argument('--url',required=True); p.add_argument('--out',required=True)
    a=p.parse_args(); print(json.dumps(attempt(a.key,a.url,a.out), ensure_ascii=False))
