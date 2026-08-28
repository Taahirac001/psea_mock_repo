export type ResendKind = "order_confirmation" | "shipping_confirmation";

export function resendCustomerEmail(
  customerId: string,
  email: string,
  kind: ResendKind,
): { ok: boolean } {
  if (!customerId.trim() || !email.trim()) {
    return { ok: false };
  }
  return { ok: true };
}
