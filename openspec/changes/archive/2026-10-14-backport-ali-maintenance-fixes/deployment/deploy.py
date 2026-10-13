"""Execute on ali: deploy the prevalidated stable overlay with a stopped-volume backup."""

import json
import os
import re
import shutil
import sqlite3
import subprocess
import time
import urllib.request
from pathlib import Path

patch = Path("/opt/codex-lb/patches/20261014-maintenance")
backup = Path("/opt/codex-lb/backups/20261014-maintenance")
compose = Path("/opt/codex-lb/compose.yaml")
volume = Path("/var/lib/docker/volumes/codex-lb-data/_data")
image = "codex-lb:1.24.0-ali-hotfix-20261014-1"


def run(args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=180)
    if result.returncode:
        raise RuntimeError("Command failed: " + args[0] + " " + args[1])
    return result.stdout


old = json.loads(run(["docker", "inspect", "codex-lb"]))[0]
manifest = json.loads((patch / "PATCH_MANIFEST.json").read_text())
if old["Image"] != manifest["base_image_id"]:
    raise RuntimeError("Installed image changed since validation")
run(["docker", "image", "tag", old["Image"], "codex-lb:ali-before-maintenance-20261014"])
if old["Config"]["Image"] == image:
    raise SystemExit("Patch image already deployed; inspect readiness before any further action.")
original = compose.read_text()
new, count = re.subn(
    r'(^\s*image:\s*)["\']?codex-lb:1\.24\.0-ali-hotfix-20261013-2["\']?(\s*(?:#.*)?$)',
    lambda match: match.group(1) + image + match.group(2),
    original,
    flags=re.MULTILINE | re.IGNORECASE,
)
if count != 1:
    raise RuntimeError("Unexpected image configuration")
staged = compose.with_name("compose.hotfix-staged.yaml")
staged.write_text(new)
os.chmod(staged, compose.stat().st_mode & 0o777)
run(["docker", "compose", "-f", str(staged), "config", "--quiet"])
backup.mkdir(parents=True, exist_ok=True)
os.chmod(backup, 0o700)
for name in ["compose.yaml", ".env"]:
    source = compose.parent / name
    if source.exists():
        shutil.copy2(source, backup / name)
        os.chmod(backup / name, 0o600)
metadata = {
    "original_image_id": old["Image"],
    "original_image_name": old["Config"]["Image"],
    "patch_image": image,
    "readiness_timeout_seconds": 240,
    "database_migrations": False,
}
(backup / "deployment.json").write_text(json.dumps(metadata, indent=2) + "\n")
os.chmod(backup / "deployment.json", 0o600)
rollback = patch / "rollback.sh"
rollback.write_text(
    "#!/bin/sh\nset -eu\n"
    "if ! docker image inspect codex-lb:ali-before-maintenance-20261014 >/dev/null 2>&1; then\n"
    "  docker image load -i /opt/codex-lb/backups/20261014-maintenance/image-before.tar >/dev/null\n"
    "fi\n"
    "docker image tag codex-lb:ali-before-maintenance-20261014 codex-lb:1.24.0-ali-hotfix-20261013-2\n"
    "cp /opt/codex-lb/backups/20261014-maintenance/compose.yaml /opt/codex-lb/compose.yaml\n"
    "docker compose -f /opt/codex-lb/compose.yaml up -d --no-deps --no-build --pull never server\n"
)
os.chmod(rollback, 0o700)
print("STAGE previous-image-backup", flush=True)
image_backup = backup / "image-before.tar"
run(["docker", "image", "save", "-o", str(image_backup), "codex-lb:ali-before-maintenance-20261014"])
os.chmod(image_backup, 0o600)
print("IMAGE_BACKUP_BYTES", image_backup.stat().st_size, flush=True)
stopped = False
started = time.monotonic()
try:
    print("STAGE graceful-stop", flush=True)
    run(["docker", "stop", "--time", "90", "codex-lb"])
    stopped = True
    print("STAGE consistent-volume-snapshot", flush=True)
    archive = backup / "data-volume.tar"
    run(["tar", "-cf", str(archive), "-C", str(volume), "."])
    os.chmod(archive, 0o600)
    connection = sqlite3.connect("file:" + str(volume / "store.db") + "?mode=ro", uri=True)
    check = connection.execute("pragma quick_check").fetchone()[0]
    revision = connection.execute("select version_num from alembic_version").fetchall()
    connection.close()
    if check != "ok":
        raise RuntimeError("Database quick_check failed")
    print(
        "SNAPSHOT",
        json.dumps({"bytes": archive.stat().st_size, "quick_check": check, "revision": revision}),
        flush=True,
    )
    print("STAGE recreate-patched-service", flush=True)
    os.replace(staged, compose)
    run(["docker", "compose", "-f", str(compose), "up", "-d", "--no-deps", "--no-build", "--pull", "never", "server"])
    ready = False
    deadline = time.monotonic() + 240
    last_report = time.monotonic()
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen("http://127.0.0.1:22455/health/ready", timeout=3) as response:
                if response.status == 200 and json.load(response).get("status") == "ok":
                    ready = True
                    break
        except Exception:
            pass
        if time.monotonic() - last_report >= 30:
            print("STAGE awaiting-cold-start", round(time.monotonic() - started, 1), flush=True)
            last_report = time.monotonic()
        time.sleep(1)
    if not ready:
        raise RuntimeError("Patched service did not become ready within 240 seconds")
    current = json.loads(run(["docker", "inspect", "codex-lb"]))[0]
    if current["Config"]["Image"] != image:
        raise RuntimeError("Unexpected deployed image")
    result = {
        "image": image,
        "image_id": current["Image"],
        "ready": True,
        "cutover_seconds": round(time.monotonic() - started, 1),
        "backup": str(backup),
        "rollback": str(rollback),
    }
    (patch / "deployment-result.json").write_text(json.dumps(result, indent=2) + "\n")
    print("DEPLOYED", json.dumps(result), flush=True)
except BaseException:
    if stopped:
        print("STAGE automatic-rollback", flush=True)
        subprocess.run([str(rollback)], capture_output=True, text=True, timeout=180)
    raise
