# Release and source status

The existing repository and historical commit returned 404 through the connected GitHub API on 31 October 2026. Local commit `68e9b05` contains aggregate result files under `paper/`. Remote/public availability is not confirmed. No repository visibility change, public upload or editor communication was performed.

A whitelist-based source/aggregate review-bundle builder is retained at `paper/release/build_review_bundle.py`. The generated ZIP is a local review candidate only; its manifest lists files/hashes and reproduction limits. Publication remains pending author approval and accessible hosting.

The local textbook corpus uses First Aid and Pathoma files from the MedQA distribution. The MedQA paper's document-collection section states that textbook release is under a research-use-only agreement: https://arxiv.org/html/2009.13081 . This statement establishes the described source distribution, not proof that the present authors accepted the required agreement or have redistribution rights. No separate local signed/license agreement was found in the inspected dataset metadata. Authors/institution must confirm the applicable acquisition/use basis before submission. Books and derived copied passages are excluded from the proposed public artifact. Source replacement would require a new corpus version and rerunning affected retrieval/generation results.

The manuscript should report observed provenance and release status factually, without internal to-do phrases or an unsupported assertion of public availability/rights clearance. An independent matched replication of the base paper still requires its question selection, implementation, prompts/scorer and settings; the external-results table cannot resolve those missing materials.
