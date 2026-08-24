-- Read-only checks for orders stuck in payment_pending.
-- Run against the orders reporting replica. Nothing here writes.

-- 1. How bad is it, and since when.
SELECT count(*)                AS stuck_orders,
       min(o.updated_at)       AS oldest_stuck,
       max(o.updated_at)       AS newest_stuck
FROM orders o
WHERE o.state = 'payment_pending'
  AND EXISTS (SELECT 1 FROM payments p
              WHERE p.order_id = o.id AND p.capture_state = 'captured');


-- 2. The head-of-line event: the first unapplied event after the cursor.
--    This is the one event that is holding up everything behind it.
SELECT e.seq,
       e.order_id,
       e.event_type,
       e.created_at,
       o.state                 AS order_state,
       (SELECT count(*) FROM payment_events b WHERE b.seq > c.seq) AS backlog
FROM payment_events_cursor c
JOIN payment_events e ON e.seq > c.seq
JOIN orders o ON o.id = e.order_id
ORDER BY e.seq
LIMIT 1;


-- 3. Money state for the blocking order — the step-0 check in
--    ops/quarantine_blocking_event.py. If capture_state = 'captured' and no
--    refund row comes back, that customer is still holding the charge and
--    the refund has to be raised BEFORE the event is quarantined.
SELECT p.order_id,
       o.state                 AS order_state,
       p.auth_state,
       p.capture_state,
       p.amount_minor,
       p.currency,
       p.captured_at,
       r.id                    AS refund_id,
       r.status                AS refund_status,
       r.created_at            AS refunded_at
FROM payments p
JOIN orders o  ON o.id = p.order_id
LEFT JOIN refunds r ON r.order_id = p.order_id
WHERE p.order_id = :order_id;          -- e.g. 'ord-48120'
