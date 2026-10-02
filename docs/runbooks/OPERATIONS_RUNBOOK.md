# Solar Operations OS — Enterprise Operations Runbook

**Classification:** Internal Confidential / SRE & Operations  
**Audience:** Platform Architects, Site Reliability Engineers, EPC Compliance Officers

---

## 1. Disaster Recovery & Backup / Restore Drill

### 1.1 Recovery Objectives
- **RPO (Recovery Point Objective):** < 15 minutes (continuous WAL archiving to S3)
- **RTO (Recovery Time Objective):** < 1 hour to full tenant service restoration

### 1.2 Automated Point-in-Time Recovery (PITR) Procedure
1. **Freeze Traffic:** Route DNS to maintenance splash page.
2. **Restore PostgreSQL 16 Base Backup:**
   ```bash
   pg_restore -h $DB_HOST -p $DB_PORT -U $DB_ADMIN -d solar_operations base_backup.dump
   ```
3. **Replay Transaction Logs (WAL):** Replay forward to target restore timestamp:
   ```conf
   recovery_target_time = '2026-10-02 04:00:00 UTC'
   recovery_target_action = 'promote'
   ```
4. **Audit Hash-Chain Verification Drill:** Execute the verification drill across 100% of audit event records:
   ```bash
   python -m app.modules.platform.audit_service --verify-all-chains
   ```

---

## 2. Cryptographic Audit Hash-Chain Verification

The platform maintains an append-only, tamper-evident SHA-256 hash chain per organization:
$$\text{event\_hash}_n = \text{SHA256}(\text{prev\_hash}_{n-1} + \text{payload}_n + \text{timestamp}_n)$$

### 2.1 Periodic HMAC-SHA256 Checkpointing
- Every 1,000 events or every 24 hours, the system creates an `AuditCheckpoint`.
- Checkpoints are signed with an off-database HMAC key (`AUDIT_CHECKPOINT_HMAC_KEY`).
- Any manual modification, deletion, or insertion within the database immediately breaks the chain and triggers an alert.

---

## 3. Offline Mobile Sync Reconciliation & Chaos Handling

Field technicians using the Android application queue mutations locally in SQLite / Room.
- **Idempotency Keys:** Every mutation includes a client UUID (`mutation_id`). Retried packets over flaky cellular connections are detected and acknowledged without duplicate execution.
- **Conflict Handling:** Server-locked entities (e.g., approved WCRs, sealed audit logs) reject incoming mutations with `409 Conflict`.
- **Clock Drift:** Server validates client timestamps against server reception windows; causal sequence numbers (`sequence_num`) dictate event ordering.

---

## 4. Bitemporal Regulations Management

Regulations in Solar Operations OS have two temporal axes:
1. **Valid Time (Effective Period):** The legal period during which a rule applies (`effective_from` to `effective_until`).
2. **Transaction Time:** When the record was created or amended in the system.

When auditing historical plants, queries execute against the regulation in force on the date of project sanction or commissioning, not the current regulation.
