"""Order states and the transitions that are allowed between them.

An order's state is only ever changed here. The fulfilment worker applies
payment events through apply_event(); nothing else writes order.state.

`cancelled` is terminal on purpose. Once an order is cancelled nothing may
move it forward again -- not a capture, not a fulfilment. A capture that
arrives for a cancelled order is a real situation (the customer cancelled
while the provider callback was already in flight) and it is money that has
to be dealt with on the payments side; it is NOT something this state
machine is allowed to paper over by advancing the order anyway.
"""

CREATED = "created"
AUTHORIZED = "authorized"
PAYMENT_PENDING = "payment_pending"
PAID = "paid"
FULFILLING = "fulfilling"
FULFILLED = "fulfilled"
CANCELLED = "cancelled"

# state -> event_type -> next state
TRANSITIONS = {
    CREATED: {"payment.authorized": AUTHORIZED, "order.cancelled": CANCELLED},
    AUTHORIZED: {"payment.pending": PAYMENT_PENDING, "order.cancelled": CANCELLED},
    PAYMENT_PENDING: {"payment.captured": PAID, "order.cancelled": CANCELLED},
    PAID: {"fulfilment.started": FULFILLING},
    FULFILLING: {"fulfilment.completed": FULFILLED},
    FULFILLED: {},
    CANCELLED: {},  # terminal — see module docstring
}


class IllegalTransition(Exception):
    """The event cannot be applied to the order in its current state."""

    def __init__(self, order_id: str, from_state: str, event_type: str):
        self.order_id = order_id
        self.from_state = from_state
        self.event_type = event_type
        super().__init__(
            f"cannot apply {event_type} to order {order_id} in state {from_state}"
        )


def apply_event(db, event) -> str:
    order = db.get_order(event.order_id)
    allowed = TRANSITIONS.get(order.state, {})
    if event.event_type not in allowed:
        raise IllegalTransition(event.order_id, order.state, event.event_type)
    order.state = allowed[event.event_type]
    db.save_order(order)
    return order.state
