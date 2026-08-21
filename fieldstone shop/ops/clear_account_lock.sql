-- Legacy ops unlock for Fieldstone Shop env-acct-01.
-- This is what the Confluence "Admin data fixes" page still documents.
-- Prefer the Help Center "Release email" action in accounts/help_center.py
-- (Priya Shah, 2026-06-12). This file does not connect to any database by itself.

UPDATE accounts
SET lock_state = 'active',
    lock_reason = NULL,
    updated_by = :operator
WHERE account_id = :account_id
  AND lock_state = 'locked_pending';
