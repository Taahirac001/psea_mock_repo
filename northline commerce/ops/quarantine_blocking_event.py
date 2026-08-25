"""Move one unappliable payment event out of the drain and advance the cursor."""

import argparse

from payments.outbox import connect, current_cursor, dead_letter, set_cursor

REASON = "illegal_transition: event cannot be applied to order in its current state"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--env", required=True, help="target environment, e.g. env-web-01")
    parser.add_argument("--seq", required=True, type=int, help="seq of the event to quarantine")
    parser.add_argument(
        "--refund-confirmed",
        action="store_true",
        help="required: the order's refund row has been checked",
    )
    args = parser.parse_args()

    if not args.refund_confirmed:
        print(
            "ABORT: refusing to quarantine a money-final event until the "
            "order's refund state has been checked. Re-run with "
            "--refund-confirmed."
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
