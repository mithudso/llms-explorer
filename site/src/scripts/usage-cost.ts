// Exact fixed-point arithmetic. Rates are user-supplied USD per million tokens.
export function usageCost(input: string, output: string, inputRate: string, outputRate: string): string | null {
  if (![input, output].every(v => /^\d{1,15}$/.test(v)) ||
      ![inputRate, outputRate].every(v => /^\d{1,9}(\.\d{1,6})?$/.test(v))) return null;
  const rate = (v: string) => {
    const [whole, fraction = ""] = v.split(".");
    return BigInt(whole) * 1000000n + BigInt(fraction.padEnd(6, "0"));
  };
  const micro = (BigInt(input) * rate(inputRate) + BigInt(output) * rate(outputRate) + 500000n) / 1000000n;
  return "$" + (micro / 1000000n).toString() + "." + (micro % 1000000n).toString().padStart(6, "0");
}
