export type CustomerLookup = {
  customerId: string;
  email: string;
};

export function lookupCustomer(email: string): CustomerLookup | null {
  const normalized = email.trim().toLowerCase();
  if (!normalized) return null;
  return {
    customerId: "",
    email: normalized,
  };
}
