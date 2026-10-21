PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Notes</title>
<style>
  :root { --bg: #f6f7fb; --card: #ffffff; --ink: #1d2433; --muted: #6b7385; --accent: #3b5bdb; --line: #e3e6ef; --danger: #c92a2a; }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: system-ui, -apple-system, Segoe UI, sans-serif; background: var(--bg); color: var(--ink); }
  main { max-width: 720px; margin: 0 auto; padding: 32px 16px; }
  h1 { margin: 0 0 4px; font-size: 28px; }
  p.sub { margin: 0 0 24px; color: var(--muted); }
  form, article { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 16px; }
  form { display: grid; gap: 10px; margin-bottom: 24px; }
  input, textarea { font: inherit; padding: 10px 12px; border: 1px solid var(--line); border-radius: 8px; width: 100%; }
  textarea { min-height: 90px; resize: vertical; }
  button { font: inherit; border: 0; border-radius: 8px; padding: 10px 14px; cursor: pointer; }
  button.add { background: var(--accent); color: #fff; justify-self: start; }
  button.del { background: transparent; color: var(--danger); padding: 4px 8px; }
  #error { color: var(--danger); min-height: 1em; margin: 0; }
  #notes { display: grid; gap: 12px; }
  article header { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
  article h2 { margin: 0; font-size: 18px; overflow-wrap: anywhere; }
  article p { margin: 8px 0; white-space: pre-wrap; overflow-wrap: anywhere; }
  article time, .empty { color: var(--muted); font-size: 13px; }
</style>
</head>
<body>
<main>
  <h1>Notes</h1>
  <p class="sub">Typed Python 3.15 on the standard library</p>
  <form id="form">
    <input id="title" placeholder="Title" maxlength="120" required>
    <textarea id="body" placeholder="Write something" maxlength="2000"></textarea>
    <button class="add" type="submit">Add note</button>
    <p id="error"></p>
  </form>
  <section id="notes"></section>
</main>
<script>
  const notes = document.getElementById("notes");
  const error = document.getElementById("error");

  function card(note) {
    const article = document.createElement("article");
    const header = document.createElement("header");
    const title = document.createElement("h2");
    const remove = document.createElement("button");
    const body = document.createElement("p");
    const time = document.createElement("time");
    title.textContent = note.title;
    remove.textContent = "Delete";
    remove.className = "del";
    remove.onclick = async () => { await fetch(`/api/notes/${note.id}`, { method: "DELETE" }); load(); };
    body.textContent = note.body;
    time.textContent = new Date(note.created_at).toLocaleString();
    header.append(title, remove);
    article.append(header, body, time);
    return article;
  }

  async function load() {
    const list = await (await fetch("/api/notes")).json();
    notes.replaceChildren(...list.map(card));
    if (!list.length) notes.innerHTML = '<p class="empty">No notes yet.</p>';
  }

  document.getElementById("form").onsubmit = async (event) => {
    event.preventDefault();
    const response = await fetch("/api/notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: document.getElementById("title").value, body: document.getElementById("body").value }),
    });
    if (!response.ok) { error.textContent = (await response.json()).error; return; }
    error.textContent = "";
    event.target.reset();
    load();
  };

  load();
</script>
</body>
</html>
"""
