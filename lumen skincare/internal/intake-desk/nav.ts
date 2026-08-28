export type NavItem = {
  id: string;
  label: string;
  href?: string;
  children?: NavItem[];
};

export const nav: NavItem[] = [
  { id: "orders", label: "Orders", href: "/orders" },
  { id: "customers", label: "Customers", href: "/customers" },
  {
    id: "extras",
    label: "Extras",
    children: [{ id: "emails", label: "Emails", href: "/extras/emails" }],
  },
];
