"""Execute on ali after revision-2 isolated validation; retain the stable rollback."""

import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request

patch = Path('/opt/codex-lb/patches/20261013-reliability')
compose = Path('/opt/codex-lb/compose.yaml')
previous = 'codex-lb:1.24.0-ali-hotfix-20261013-1'
image = 'codex-lb:1.24.0-ali-hotfix-20261013-2'
original = compose.read_text()
if original.count(previous) != 1:
    raise SystemExit('Unexpected deployed revision')
saved = patch / 'compose-revision1.yaml'
saved.write_text(original)
os.chmod(saved, 0o600)
staged = compose.with_name('compose.hotfix-staged.yaml')
staged.write_text(original.replace(previous, image))
os.chmod(staged, compose.stat().st_mode & 0o777)
subprocess.run(['docker', 'compose', '-f', str(staged), 'config', '--quiet'], check=True)
started = time.monotonic()
try:
    print('STAGE graceful-revision2-cutover', flush=True)
    subprocess.run(['docker', 'stop', '--time', '90', 'codex-lb'], check=True, capture_output=True)
    os.replace(staged, compose)
    subprocess.run(
        ['docker', 'compose', '-f', str(compose), 'up', '-d', '--no-deps', '--no-build', '--pull', 'never', 'server'],
        check=True, capture_output=True,
    )
    deadline = time.monotonic() + 240
    last_report = time.monotonic()
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen('http://127.0.0.1:22455/health/ready', timeout=3) as response:
                if response.status == 200 and json.load(response).get('status') == 'ok':
                    break
        except Exception:
            pass
        if time.monotonic() - last_report >= 30:
            print('STAGE awaiting-cold-start', round(time.monotonic() - started, 1), flush=True)
            last_report = time.monotonic()
        time.sleep(1)
    else:
        raise RuntimeError('Revision 2 did not become ready within 240 seconds')
    current = json.loads(subprocess.check_output(['docker', 'inspect', 'codex-lb']))[0]
    if current['Config']['Image'] != image:
        raise RuntimeError('Unexpected deployed image')
    result = {
        'image': image,
        'image_id': current['Image'],
        'ready': True,
        'cutover_seconds': round(time.monotonic() - started, 1),
        'backup': '/opt/codex-lb/backups/20261013-reliability-final',
        'rollback': str(patch / 'rollback.sh'),
    }
    (patch / 'deployment-result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('DEPLOYED', json.dumps(result), flush=True)
except BaseException:
    print('STAGE restore-healthy-revision1', flush=True)
    compose.write_text(original)
    subprocess.run(
        ['docker', 'compose', '-f', str(compose), 'up', '-d', '--no-deps', '--no-build', '--pull', 'never', 'server'],
        check=True, capture_output=True,
    )
    raise
