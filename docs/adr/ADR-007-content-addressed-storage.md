# ADR-007: Content-Addressed Document Storage

**Status:** Accepted  
**Date:** 2026-10-01

## Context

Documents (PDFs, images, certificates) must be stored durably and verifiably. The same physical file uploaded multiple times (e.g., certificate shared across projects) should not be duplicated. Generated documents must be immutable and their content verifiable.

## Decision

**Content-addressed storage with SHA-256 as the key.**

Upload flow:
1. Client uploads file to a pre-upload endpoint or directly via multipart.
2. API streams the file, computes `SHA-256` digest in-flight.
3. Key in object store: `{org_id}/{sha256_hex[0:2]}/{sha256_hex[2:4]}/{sha256_hex}` (like Git object storage).
4. If the key already exists, skip the upload (deduplication).
5. `DocumentVersion.content_hash = sha256_hex`, `storage_key = <computed key>`.

Access: signed URLs (TTL 15 minutes for normal access, 5 minutes for download). The signing key is per-organization, rotated annually.

Antivirus hook: after upload, a background job scans the blob. Until scan passes, the document version is in `quarantined` state and cannot be verified or used in compliance.

## Alternatives Considered

- **Random UUID object keys** — No deduplication, no content-addressability, cannot verify integrity at rest.
- **Per-org prefixed path** — Adopted within the content-addressed scheme for RLS-like isolation at the storage layer.

## Consequences

- **Good:** Natural deduplication. Integrity verification by recomputing hash. Immutable blobs (if a document "changes", a new version is created with a new hash; old version is retained).
- **Good:** Hash serves as content fingerprint — can detect corruption at rest.
- **Risk:** Hash collisions are cryptographically negligible for SHA-256.
- **Risk:** Deduplication across orgs leaks information (timing side-channel). Mitigation: deduplication is per-org only (prefix includes org_id).
