const KIND_LABELS = {
  DEPOSIT: "Deposit",
  WITHDRAW: "Withdraw",
  TRANSFER_IN: "Transfer in",
  TRANSFER_OUT: "Transfer out",
};

const INFLOWS = new Set(["DEPOSIT", "TRANSFER_IN"]);

export const kindLabel = (kind) => KIND_LABELS[kind] || kind;

export const kindClass = (kind) => (INFLOWS.has(kind) ? "in" : "out");

export const signed = (kind, amount) => `${INFLOWS.has(kind) ? "+" : "-"}${amount}`;

export const money = (amount) => `$${amount}`;

export const dateTime = (iso) =>
  new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
