"""Retired. Kept only so old deploy references resolve.

Admin sign-in for env-web-01 moved to the shared platform gateway. Nothing
in the order pipeline imports or reads this module, and it takes no part in
how an order moves between states.

The order pipeline is: payments/capture_handler.py (records payments),
fulfillment/event_drain.py (applies events to orders),
orders/state_machine.py (the states themselves).
"""
