"""Clear a head-of-line block in the payment-event drain.

Run this when orders are stuck in `payment_pending` because one event at the
head of `payment_events` cannot be applied and the cursor will not move past
it (fulfillment/event_drain.py). This is an operator action: runtime data
only, no deploy, no code change, no release.

    python ops/quarantine_blocking_event.py --env env-web-01 --seq <seq>

WHAT IT DOES
    1. moves that one event into payment_events_dead_letter, with the reason
    2. advances the cursor past it by exactly one
    3. lets the worker drain the backlog that was stuck behind it

STEP 0 -- DO THIS FIRST, IT IS NOT OPTIONAL
-------------------------------------------
Find out what the blocking event actually is and whether the money on it has
already been dealt with. ops/stuck_orders.sql has the two queries: the head
event, and the payment + refund state for its order.

A `payment.captured` blocked on a `cancelled` order means the customer was
charged for an order that is not going to ship. Quarantining that event
clears the queue and makes the symptom go away for everyone else -- and
leaves that one customer charged with nothing coming, and no longer visible
in any stuck-order report. That is a worse outcome than the outage.

So, before quarantining, check the refund state of the blocking order:

  * a refund already exists for it -- the cancellation was settled, the
    capture event is genuinely moot. Quarantine it and move on.

  * no refund exists -- the customer is still holding that charge. Raise the
    refund for that order FIRST, confirm it, and only then quarantine. Do
    not reverse this order of operations.

AFTER
-----
The cursor advances by one and the worker drains the backlog on its next
pass. Verify all three, and do not close the incident on the first one:

  a) fulfillment-worker logs `drained` with the backlog count falling, and
     no new `apply failed seq=<same seq>` lines
  b) the stuck-order count from ops/stuck_orders.sql returns to 0
  c) the orders that were stuck now read `paid` (then `fulfilling`), and the
     quarantined order is still `cancelled` -- it must not have advanced

If a second event blocks immediately behind the first, do not loop this
script. Two unappliable events in a row means the state machine and the
event stream disagree more broadly, and that needs a look at
orders/state_machine.py before anything else is quarantined.
"""

import argparse

from payments.outbox import connect, current_cursor, dead_letter, set_cursor

REASON = "illegal_transition: event cannot be applied to order in its current state"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--env", required=True)
    parser.add_argument("--seq", required=True, type=int)
    parser.add_argument(
        "--refund-confirmed",
        action="store_true",
        help=(
            "acknowledge step 0: the blocking order's money is settled — a "
            "refund exists, or the event is not a capture"
        ),
    )
    args = parser.parse_args()

    if not args.refund_confirmed:
        print(
            "ABORT: step 0 not acknowledged. Check the blocking order's "
            "payment and refund state (ops/stuck_orders.sql) before "
            "quarantining, then re-run with --refund-confirmed."
        )
        return 1

    db = connect(args.env)
    cursor = current_cursor(db)
    if args.seq != cursor + 1:
        print(
            f"ABORT: seq {args.seq} is not the head of line "
            f"(cursor is at {cursor}, head is {cursor + 1}). Quarantining "
            "anything other than the head event would skip live events."
        )
        return 1

    dead_letter(db, seq=args.seq, reason=REASON)
    set_cursor(db, args.seq)
    print(f"quarantined seq={args.seq}; cursor advanced to {args.seq}")
    print("now verify: backlog falling, stuck count 0, quarantined order still cancelled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
