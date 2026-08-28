type SellingPlanAllocation = { sellingPlan: { id: string } } | null;

type CartLine = {
  quantity: number;
  sellingPlanAllocation: SellingPlanAllocation;
  merchandise: { id: string };
};

type FunctionInput = {
  cart: { lines: CartLine[] };
  discountNode: { metafield: { value: string } | null };
};

type FunctionRunResult = {
  discounts: Array<{
    value: { percentage: { value: string } };
    targets: Array<{ productVariant: { id: string } }>;
    message: string;
  }>;
};

const EMPTY_DISCOUNT: FunctionRunResult = { discounts: [] };

export function run(input: FunctionInput): FunctionRunResult {
  const configuration = JSON.parse(
    input?.discountNode?.metafield?.value ?? "{}"
  );
  const code = configuration.discountCode ?? "WELCOME15";
  const percent = Number(configuration.percent ?? 15);

  const hasSellingPlan = input.cart.lines.some(
    (line) => line.sellingPlanAllocation !== null
  );
  if (hasSellingPlan) {
    return EMPTY_DISCOUNT;
  }

  const targets = input.cart.lines
    .filter((line) => line.merchandise?.id)
    .map((line) => ({ productVariant: { id: line.merchandise.id } }));

  if (targets.length === 0) {
    return EMPTY_DISCOUNT;
  }

  return {
    discounts: [
      {
        value: { percentage: { value: String(percent) } },
        targets,
        message: code,
      },
    ],
  };
}
