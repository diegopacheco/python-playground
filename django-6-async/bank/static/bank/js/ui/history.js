import { dateTime, kindClass, kindLabel, money, signed } from "../format.js";
import { state } from "../store.js";

const body = document.getElementById("ledger-body");
const empty = document.getElementById("ledger-empty");

function row(entry) {
  return `<tr>
    <td>${dateTime(entry.created_at)}</td>
    <td><span class="kind ${kindClass(entry.kind)}">${kindLabel(entry.kind)}</span></td>
    <td>${entry.counterparty || "—"}</td>
    <td class="num">${signed(entry.kind, money(entry.amount))}</td>
    <td class="num">${money(entry.balance_after)}</td>
  </tr>`;
}

export function renderHistory() {
  body.innerHTML = state.transactions.map(row).join("");
  empty.hidden = state.transactions.length > 0;
}
