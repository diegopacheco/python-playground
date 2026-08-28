import { api } from "../api.js";
import { money } from "../format.js";
import { reload, state } from "../store.js";
import { flash } from "./flash.js";

const target = document.getElementById("transfer-target");

function submits(formId, action, done) {
  const form = document.getElementById(formId);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!state.profile) return flash("Open an account first", "error");
    const data = new FormData(form);
    try {
      const result = await action(state.profile.account.id, data);
      form.reset();
      await reload();
      flash(done(result));
    } catch (error) {
      flash(error.message, "error");
    }
  });
}

export function mountMoney() {
  submits(
    "deposit-form",
    (accountId, data) => api.deposit(accountId, data.get("amount")),
    (entry) => `Deposited ${money(entry.amount)} — balance ${money(entry.balance_after)}`,
  );

  submits(
    "withdraw-form",
    (accountId, data) => api.withdraw(accountId, data.get("amount")),
    (entry) => `Withdrew ${money(entry.amount)} — balance ${money(entry.balance_after)}`,
  );

  submits(
    "transfer-form",
    (accountId, data) =>
      api.transfer(accountId, Number(data.get("target_account_id")), data.get("amount")),
    ({ sent }) =>
      `Sent ${money(sent.amount)} to ${sent.counterparty} — balance ${money(sent.balance_after)}`,
  );
}

export function renderMoney() {
  const mine = state.profile?.account.id;
  const others = state.accounts.filter((account) => account.id !== mine);

  target.innerHTML = others
    .map((a) => `<option value="${a.id}">${a.owner} · ${a.number}</option>`)
    .join("");
  target.disabled = others.length === 0;
}
