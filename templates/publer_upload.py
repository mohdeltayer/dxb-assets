#!/usr/bin/env python3
"""Upload a finished Reel to Publer's media library with the media-only key (advisor Phase 1 step 3, 25 Oct 2026).

    python templates/publer_upload.py <reel.mp4> <receipt.json>

Reads PUBLER_MEDIA_KEY (scopes: media, workspaces) and, optionally, PUBLER_WORKSPACE (the workspace name,
default "The Digi-Lounge"). Looks the workspace up with the key, uploads the file directly (in the library,
named after the file, so the connector finds it by name), retries once, and writes a receipt:
status (uploaded / failed / no key), name, bytes, seconds, time, and the media id only when REPO_PRIVATE is
"true" (no Publer ids in public files). Prints the status line only, never a key, an id or a response body.
Exit 0 on upload, 1 otherwise; the workflow step never fails the job on it.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

API = 'https://app.publer.com/api/v1'
WORKSPACE = os.environ.get('PUBLER_WORKSPACE', 'The Digi-Lounge')


def _curl(args, key, workspace=None, timeout=240):
    """Run curl with the auth headers passed through a config file, so the key never sits on a command line."""
    with tempfile.NamedTemporaryFile('w', suffix='.cfg', delete=False) as cfg:
        cfg.write(f'header = "Authorization: Bearer-API {key}"\n')
        if workspace:
            cfg.write(f'header = "Publer-Workspace-Id: {workspace}"\n')
    try:
        r = subprocess.run(['curl', '-sS', '--max-time', str(timeout), '-K', cfg.name, '-w', '\n%{http_code}'] + args,
                           capture_output=True, text=True)
    finally:
        os.unlink(cfg.name)
    body, _, code = r.stdout.rpartition('\n')
    try:
        data = json.loads(body) if body.strip() else None
    except ValueError:
        data = None
    return (int(code) if code.strip().isdigit() else 0), data


def workspace_id(key):
    code, data = _curl([f'{API}/workspaces'], key, timeout=30)
    if code != 200 or not isinstance(data, list) or not data:
        return None, f'workspace lookup failed (HTTP {code})'
    for w in data:
        if (w.get('name') or '').strip().lower() == WORKSPACE.lower():
            return w.get('id'), None
    if len(data) == 1:
        return data[0].get('id'), None
    return None, f'workspace "{WORKSPACE}" not found among {len(data)}'


def upload(path, key, ws):
    name = os.path.basename(path)
    code, data = _curl([f'{API}/media', '-F', f'file=@{path};type=video/mp4;filename={name}',
                        '-F', 'direct_upload=true', '-F', 'in_library=true'], key, ws)
    mid = (data or {}).get('id') if isinstance(data, dict) else None
    if code in (200, 201) and mid:
        return mid, None
    return None, f'upload failed (HTTP {code})'


def main(path, receipt):
    t0 = time.time()
    rec = {'name': os.path.basename(path), 'bytes': os.path.getsize(path) if os.path.exists(path) else None,
           'route': 'runner api (media-only key)'}
    key = os.environ.get('PUBLER_MEDIA_KEY', '').strip()
    mid, err = None, None
    if not key:
        err = 'no key (PUBLER_MEDIA_KEY not set)'
    elif not os.path.exists(path):
        err = 'reel not found'
    else:
        ws, err = workspace_id(key)
        if ws:
            for attempt in (1, 2):
                mid, err = upload(path, key, ws)
                if mid:
                    break
                time.sleep(5)
    rec['status'] = 'uploaded' if mid else 'failed'
    if err:
        rec['reason'] = err
    if mid and os.environ.get('REPO_PRIVATE', '').lower() == 'true':
        rec['media_id'] = mid
    rec['secs'] = round(time.time() - t0, 1)
    rec['at'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    json.dump(rec, open(receipt, 'w'), indent=1, ensure_ascii=False)
    print(f"publer upload: {rec['status']}" + (f" ({err})" if err else '') + f" in {rec['secs']} s")
    return 0 if mid else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
