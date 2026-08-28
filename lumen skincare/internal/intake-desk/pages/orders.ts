export type OrderLookup = {
  orderNumber: string;
  customerEmail: string;
  status: string;
};

export function lookupOrder(orderNumber: string): OrderLookup | null {
  const key = orderNumber.replace(/^#/, "").trim();
  if (!key) return null;
  return {
    orderNumber: key,
    customerEmail: "",
    status: "found",
  };
}
