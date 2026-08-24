-- Retired. Kept only so old runbook links resolve.
--
-- This check belonged to the edge access control that was retired when the
-- merchant admin path moved behind the shared platform gateway. It has
-- nothing to do with orders, payments, or fulfilment.
--
-- For anything about an order that has been charged but not advanced, use
-- ops/stuck_orders.sql.

SELECT 'retired: see ops/stuck_orders.sql' AS note;
