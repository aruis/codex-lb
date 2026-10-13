FROM codex-lb:1.24.0-ali-hotfix-20261013-2
LABEL local.codex-lb.patch="ali-maintenance-20261014-1"
COPY --chown=app:app app/ /app/app/
COPY PATCH_MANIFEST.json /app/PATCH_MANIFEST.json
