"""Order states and the transitions allowed between them."""

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
    # cancelled is terminal -- applying a capture here would resurrect a dead
    # order. A late capture is money to deal with on the payments side.
    CANCELLED: {},
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
