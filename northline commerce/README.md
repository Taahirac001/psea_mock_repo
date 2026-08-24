# env-web-01 — Northline Commerce (sanitized)

Storefront, checkout, and order pipeline for Northline Commerce. Built by our
platform team in 2021 and operated by us since. Northline staff do not run or
administer this stack.

| Path | What it is |
|---|---|
| `orders/state_machine.py` | The only place order state changes. `cancelled` and `fulfilled` are terminal |
| `payments/capture_handler.py` | Provider callbacks → payments row + outbox event. Never touches order state |
| `payments/outbox.py` | The `payment_events` stream and its single global cursor |
| `fulfillment/event_drain.py` | Applies events to orders in strict `seq` order; stops on an event it cannot apply |
| `ops/stuck_orders.sql` | Read-only: stuck-order count, the head-of-line event, money state for one order |
| `ops/quarantine_blocking_event.py` | Operator recovery for a head-of-line block. Runtime data only — no deploy |
| `deploy/env-web-01.yml` | Deploy descriptor |
| `config/service_map.yml` | How the four services relate |
| `edge/`, `ops/verify_edge_allowlist.sql` | Retired. The merchant admin path moved behind the shared platform gateway; nothing in the order pipeline reads any of it |

## Orders stuck in `payment_pending`

The money moved but the order did not. That is the drain, not the provider and
not `payments-api` — both of those keep logging healthy while it happens.
`fulfillment/event_drain.py` holds one global cursor and stops at the first
event it cannot apply, so a single unappliable event holds up every order
behind it and the backlog grows until someone clears the head event.

Start with `ops/stuck_orders.sql` (query 2 gives you the blocking `seq`), then
follow `ops/quarantine_blocking_event.py` — including its step 0, which is
there so that clearing the queue does not quietly leave one customer charged
for an order that was cancelled.

Do not "fix" this by making the drain skip events or by turning off
`STOP_ON_ERROR`. Out-of-order application is what those guards exist to
prevent, and it has cost us double fulfilment before.
