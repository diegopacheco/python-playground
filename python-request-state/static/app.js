const API = "/api/games";
const form = document.getElementById("game-form");
const fields = ["name", "release_year", "image_url", "description"];

async function request(method, url, body) {
  const response = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(errorText(data.detail) || response.statusText);
  }
  return response.status === 204 ? null : response.json();
}

function errorText(detail) {
  if (Array.isArray(detail)) return detail.map((d) => `${d.loc.at(-1)}: ${d.msg}`).join(", ");
  return detail;
}

function showMessage(text, isError = false) {
  const message = document.getElementById("message");
  message.textContent = text;
  message.className = isError ? "error" : "";
}

function renderGames(games) {
  const list = document.getElementById("games");
  const template = document.getElementById("card");
  list.replaceChildren();
  document.getElementById("count").textContent = `${games.length} game${games.length === 1 ? "" : "s"}`;
  if (games.length === 0) {
    list.innerHTML = '<p class="empty">No games yet.</p>';
    return;
  }
  for (const game of games) {
    const card = template.content.cloneNode(true);
    card.querySelector("img").src = game.image_url;
    card.querySelector("img").alt = game.name;
    card.querySelector("h3").textContent = game.name;
    card.querySelector(".year").textContent = game.release_year;
    card.querySelector(".desc").textContent = game.description;
    card.querySelector(".id").textContent = game.id;
    card.querySelector(".edit").onclick = () => startEdit(game);
    card.querySelector(".delete").onclick = () => removeGame(game);
    list.appendChild(card);
  }
}

async function loadGames() {
  try {
    renderGames(await request("GET", API));
  } catch (error) {
    showMessage(error.message, true);
  }
}

function startEdit(game) {
  document.getElementById("game-id").value = game.id;
  for (const field of fields) document.getElementById(field).value = game[field];
  document.getElementById("form-title").textContent = "Edit game";
  document.getElementById("submit").textContent = "Save";
  document.getElementById("cancel").hidden = false;
  showMessage("");
}

function resetForm() {
  form.reset();
  document.getElementById("game-id").value = "";
  document.getElementById("form-title").textContent = "Add game";
  document.getElementById("submit").textContent = "Create";
  document.getElementById("cancel").hidden = true;
}

async function removeGame(game) {
  if (!confirm(`Delete ${game.name}?`)) return;
  try {
    await request("DELETE", `${API}/${game.id}`);
    if (document.getElementById("game-id").value === game.id) resetForm();
    showMessage(`Deleted ${game.name}`);
    await loadGames();
  } catch (error) {
    showMessage(error.message, true);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const id = document.getElementById("game-id").value;
  const body = Object.fromEntries(fields.map((field) => [field, document.getElementById(field).value]));
  body.release_year = Number(body.release_year);
  try {
    const game = id ? await request("PUT", `${API}/${id}`, body) : await request("POST", API, body);
    resetForm();
    showMessage(`${id ? "Updated" : "Created"} ${game.name}`);
    await loadGames();
  } catch (error) {
    showMessage(error.message, true);
  }
});

document.getElementById("cancel").onclick = () => {
  resetForm();
  showMessage("");
};

loadGames();
