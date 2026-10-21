# Verification: fix-ali-image-host-selection

## Completeness

All eight tasks are complete. Both added requirement blocks are synced into
main specs. Source and tests are committed and pushed to the personal stable
branch; this record and archive follow in a documentation-only commit.

## Correctness

- Internal host selection: shared selector checks visibility and suppression;
  host matrix covers cold, partial, empty and authoritative catalogs.
- Default probes: API matrix covers both candidates, fallback and explicit
  model preservation; unit probe tests retain timeout and error behavior.
- Image generation: actual canonical and Codex alias paths tested against
  bootstrap and current catalogs. All four fail with the old API file and
  pass with the patch. Public gpt-image-2 remains in tool payload and usage
  accounting. Existing error, auth, streaming, upload and reservation tests pass.
- Editing: round-trip test asserts Luna host while retaining image content
  translation. No changes to file ownership, retries or settlement code.
- Full selected test suite: 231 passed. Ruff and affected strict specs pass.
  Full-spec validation has 21 unchanged baseline failures, recorded in context.
- Real deployed image and ordinary Responses requests pass; logs and hashes
  recorded in context. No actual image edit was sent to the paid upstream;
  editing is covered by the isolated public-route regression suite.

## Coherence

The selector is the same zero-configuration algorithm as upstream #2320.
No migration, new configuration or schema change. The runtime overlay changes
exactly three files; deployment evidence binds their hashes to source commit
070696c8 and the installed image. Backup and rollback are retained.

## Assessment

No critical verification findings. Operational notes: slow cold startup under
swap/I/O pressure; upstream image dimensions differ from the requested size.
Neither is changed by this patch. Ready to archive.
