# Database checkpoint and rollback

The source checkpoint before the improvement pass is `81f38879e949d17c66c6f42217c392efd817cd25`,
with message `CDSM before results improvement`.

On 27 October 2026, both live databases were cleanly stopped and copied into
`local_backups/before-results-improvement-20261027/`. The Neo4j cold archive is
576,843,264 bytes; the Qdrant archive is 1,948,056,576 bytes. The directory contains
SHA-256 hashes, container image IDs, inventory, a restoration script, and the
backup/restore verification log. It is ignored by Git.

The archives were restored into new Docker volumes and started with the exact
original image IDs. Restored graph counts (58,676 nodes and 649,815 relationships)
and all four Qdrant collection counts/vector configurations matched the originals.
This test completed before graph or vector data was changed.

| Database | Original container retained for rollback | Active working container |
| --- | --- | --- |
| Neo4j | `code-neo4j-1` | `cdsm-neo4j-improved-20261027` |
| Qdrant | `code-qdrant-1` | `cdsm-qdrant-improved-20261027` |

The original containers are stopped and their volumes are retained. Working
containers use the original localhost service ports. New graph data is isolated
under the `ClinicalEntity` label; old graph nodes remain in the working clone.
The active textbook collection is `medical_textbooks_v2`; the old 156-passage
collection and all pinned-source collections are retained.

To return to the old database pair, run:

```bash
bash local_backups/before-results-improvement-20261027/restore_baseline.sh
```

The script stops the working containers, starts the original pair, and restores
the old textbook collection setting without replacing provider keys. It retains
both working volumes. Preserve source edits before separately checking out the
Git checkpoint for a matching code rollback; the script does not discard code.
The private environment-file copy is local-only and must not be committed.

If the original volumes are unavailable, retain the two cold archives together
with `manifest.json`; `backup_databases.py` records the successfully tested
`docker cp` restoration sequence. Physical copies must be restored using the
image IDs in that manifest. A new checkout alone does not contain database data.
