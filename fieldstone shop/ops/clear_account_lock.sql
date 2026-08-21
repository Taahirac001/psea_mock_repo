-- env-acct-01, ops admin connection
-- account_id from the ticket

UPDATE accounts
SET lock_state = 'active',
    lock_reason = NULL,
    updated_by = :operator
WHERE account_id = :account_id
  AND lock_state = 'locked_pending';
