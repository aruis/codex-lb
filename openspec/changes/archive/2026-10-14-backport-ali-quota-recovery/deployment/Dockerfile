FROM codex-lb:1.24.0-ali-hotfix-20261014-1
LABEL local.codex-lb.patch="ali-quota-recovery-20261014-2"
COPY --chown=app:app app/ /app/app/
COPY PATCH_MANIFEST.json /app/PATCH_MANIFEST.json
