function csrfToken() {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return match ? match[1] : "";
}

async function request(method, path, body) {
  const response = await fetch(`/api${path}`, {
    method,
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
    body: body ? JSON.stringify(body) : undefined,
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || response.statusText);
  return payload;
}

export const api = {
  listProfiles: () => request("GET", "/profiles/"),
  createProfile: (full_name, email) => request("POST", "/profiles/", { full_name, email }),
  getProfile: (id) => request("GET", `/profiles/${id}/`),
  listAccounts: () => request("GET", "/accounts/"),
  deposit: (id, amount) => request("POST", `/accounts/${id}/deposit/`, { amount }),
  withdraw: (id, amount) => request("POST", `/accounts/${id}/withdraw/`, { amount }),
  statement: (id) => request("GET", `/accounts/${id}/transactions/`),
  transfer: (source_account_id, target_account_id, amount) =>
    request("POST", "/transfers/", { source_account_id, target_account_id, amount }),
};
