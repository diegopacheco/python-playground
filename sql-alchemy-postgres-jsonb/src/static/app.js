const form = document.getElementById("doc-form");
const formTitle = document.getElementById("form-title");
const nameInput = document.getElementById("name");
const dataInput = document.getElementById("data");
const formError = document.getElementById("form-error");
const searchInput = document.getElementById("contains");
const searchError = document.getElementById("search-error");
const list = document.getElementById("list");
const count = document.getElementById("count");

const SAMPLE = {
  status: "paid",
  total: 249.9,
  customer: { id: 42, tier: "gold" },
  items: [{ sku: "kbd-01", qty: 1 }],
};

let editingId = null;

const escapeHtml = (value) =>
  value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function highlight(value) {
  const json = escapeHtml(JSON.stringify(value, null, 2));
  return json.replace(
    /("(\\u[a-fA-F0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false)\b|\bnull\b|-?\d+(\.\d+)?([eE][+-]?\d+)?)/g,
    (match) => {
      let cls = "tok-num";
      if (match.startsWith('"')) cls = match.trimEnd().endsWith(":") ? "tok-key" : "tok-str";
      else if (match === "true" || match === "false") cls = "tok-bool";
      else if (match === "null") cls = "tok-null";
      return `<span class="${cls}">${match}</span>`;
    },
  );
}

async function api(path, options) {
  const response = await fetch(path, options);
  if (response.status === 204) return null;
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail ?? response.statusText);
  return body;
}

async function load() {
  const filter = searchInput.value.trim();
  const path = filter
    ? `/api/documents?contains=${encodeURIComponent(filter)}`
    : "/api/documents";
  try {
    render(await api(path));
    searchError.textContent = "";
  } catch (error) {
    searchError.textContent = String(error.message);
  }
}

function render(documents) {
  count.textContent = `${documents.length} document${documents.length === 1 ? "" : "s"}`;
  list.innerHTML = "";
  if (documents.length === 0) {
    list.innerHTML = '<li class="empty">No documents match.</li>';
    return;
  }
  for (const document_ of documents) {
    const item = document.createElement("li");
    item.innerHTML = `
      <div class="row">
        <div>
          <strong>${escapeHtml(document_.name)}</strong>
          <div class="meta">id ${document_.id} &middot; ${new Date(document_.created_at).toLocaleString()}</div>
        </div>
        <div class="row-actions">
          <button data-action="edit">Edit</button>
          <button data-action="delete">Delete</button>
        </div>
      </div>
      <pre>${highlight(document_.data)}</pre>`;
    item.querySelector('[data-action="edit"]').onclick = () => startEdit(document_);
    item.querySelector('[data-action="delete"]').onclick = () => remove(document_.id);
    list.appendChild(item);
  }
}

function startEdit(document_) {
  editingId = document_.id;
  formTitle.textContent = `Editing #${document_.id}`;
  nameInput.value = document_.name;
  dataInput.value = JSON.stringify(document_.data, null, 2);
  formError.textContent = "";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function resetForm() {
  editingId = null;
  formTitle.textContent = "New document";
  nameInput.value = "";
  dataInput.value = JSON.stringify(SAMPLE, null, 2);
  formError.textContent = "";
}

async function remove(id) {
  await api(`/api/documents/${id}`, { method: "DELETE" });
  if (editingId === id) resetForm();
  load();
}

form.onsubmit = async (event) => {
  event.preventDefault();
  let data;
  try {
    data = JSON.parse(dataInput.value);
  } catch (error) {
    formError.textContent = `Invalid JSON: ${error.message}`;
    return;
  }
  if (data === null || typeof data !== "object" || Array.isArray(data)) {
    formError.textContent = "Payload must be a JSON object.";
    return;
  }
  try {
    await api(editingId ? `/api/documents/${editingId}` : "/api/documents", {
      method: editingId ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: nameInput.value, data }),
    });
    resetForm();
    load();
  } catch (error) {
    formError.textContent = String(error.message);
  }
};

document.getElementById("format").onclick = () => {
  try {
    dataInput.value = JSON.stringify(JSON.parse(dataInput.value), null, 2);
    formError.textContent = "";
  } catch (error) {
    formError.textContent = `Invalid JSON: ${error.message}`;
  }
};

document.getElementById("clear-form").onclick = resetForm;
document.getElementById("search").onclick = load;
document.getElementById("clear-search").onclick = () => {
  searchInput.value = "";
  load();
};
searchInput.onkeydown = (event) => {
  if (event.key === "Enter") load();
};

resetForm();
load();
