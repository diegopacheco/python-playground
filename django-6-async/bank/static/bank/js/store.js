import { api } from "./api.js";

const listeners = [];

export const state = { profiles: [], accounts: [], profile: null, transactions: [] };

export function subscribe(listener) {
  listeners.push(listener);
}

function publish() {
  listeners.forEach((listener) => listener(state));
}

export async function reload(profileId = state.profile?.id) {
  const [{ profiles }, { accounts }] = await Promise.all([
    api.listProfiles(),
    api.listAccounts(),
  ]);
  state.profiles = profiles;
  state.accounts = accounts;
  const selected = profiles.find((p) => p.id === profileId) || profiles[0] || null;
  state.profile = selected;
  state.transactions = selected
    ? (await api.statement(selected.account.id)).transactions
    : [];
  publish();
}
