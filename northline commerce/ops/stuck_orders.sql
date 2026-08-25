-- Read-only checks for orders stuck in payment_pending.
-- Run against the orders reporting replica. Nothing here writes, and ad-hoc
-- sessions have no write grants on the pipeline tables on the primary
-- either -- runtime changes go through the ops/ tooling.

-- 1. Stuck-order count
SELECT count(*)                AS stuck_orders,
       min(o.updated_at)       AS oldest_stuck,
       max(o.updated_at)       AS newest_stuck
FROM orders o
WHERE o.state = 'payment_pending'
  AND EXISTS (SELECT 1 FROM payments p
              WHERE p.order_id = o.id AND p.capture_state = 'captured');


-- 2. Head-of-line event (first unapplied event after the cursor)
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


-- 3. Money state for one order
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
WHERE p.order_id = :order_id;
