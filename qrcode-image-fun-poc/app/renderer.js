const SERVER = "http://127.0.0.1:8000";
const TABS = ["upload", "page", "scan", "pairs"];
const SCAN_INTERVAL_MS = 700;

const SHORTCUTS = [
  ["Search", "⌘ K"],
  ["Shortcuts", "⌘ /"],
  ["Zoom in / out", "⌘ + / ⌘ -"],
  ["Go to tab 1-4", "⌘ 1 .. ⌘ 4"],
  ["Capture the screen", "⌘ P"],
  ["Full screen", "⌘ ⇧ ↩"],
  ["Cut / copy / paste", "⌘ X / ⌘ C / ⌘ V"],
];

const el = (id) => document.getElementById(id);
let current = null;
let stream = null;
let scanTimer = null;
let inFlight = false;

function toast(message) {
  const box = el("toast");
  box.textContent = message;
  box.classList.add("show");
  clearTimeout(box.timer);
  box.timer = setTimeout(() => box.classList.remove("show"), 2600);
}

function goto(tab) {
  TABS.forEach((name) => {
    el(name).classList.toggle("active", name === tab);
    document
      .querySelector(`nav button[data-tab="${name}"]`)
      .classList.toggle("active", name === tab);
  });
  if (tab !== "scan") stopCamera();
  if (tab === "pairs") loadPairs();
}

async function serverHealth() {
  try {
    await fetch(`${SERVER}/pairs`);
    el("server-state").textContent = "up";
  } catch {
    el("server-state").textContent = "down — run ./run.sh";
  }
}

function showPage(entry) {
  current = entry;
  const url = `${SERVER}/pages/${entry.id}.png?t=${Date.now()}`;
  el("page-img").src = url;
  el("print-img").src = url;
}

async function upload(file) {
  const body = new FormData();
  body.append("image", file, file.name || "upload.png");
  const response = await fetch(`${SERVER}/uploads`, { method: "POST", body });
  if (!response.ok) {
    toast(`Upload rejected: ${(await response.json()).detail}`);
    return;
  }
  const entry = await response.json();
  el("result-id").textContent = entry.id;
  el("result-style").textContent = `image strength ${entry.image_strength} on attempt ${entry.style_attempt}`;
  el("result-mm").textContent = entry.code_mm;
  el("upload-result").hidden = false;
  showPage(entry);
  toast("Page minted and gated");
}

async function startCamera() {
  if (!(await window.desktop.askCamera())) {
    toast("Camera access denied in System Settings");
    return;
  }
  stream = await navigator.mediaDevices.getUserMedia({
    video: { width: { ideal: 1920 }, height: { ideal: 1080 } },
  });
  el("video").srcObject = stream;
  await el("video").play();
  el("scan-toggle").textContent = "Stop camera";
  el("shoot").disabled = false;
  el("scan-state").textContent = "looking for a code";
  scanTimer = setInterval(() => sendScan(true), SCAN_INTERVAL_MS);
}

function stopCamera() {
  clearInterval(scanTimer);
  scanTimer = null;
  if (stream) stream.getTracks().forEach((track) => track.stop());
  stream = null;
  el("video").srcObject = null;
  el("scan-toggle").textContent = "Start camera";
  el("shoot").disabled = true;
  el("scan-state").textContent = "idle";
}

function refusal(body) {
  const detail = body?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => `${item.loc?.join(".")}: ${item.msg}`).join("; ");
  }
  return "refused for an unknown reason";
}

function readCode() {
  const video = el("video");
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const context = canvas.getContext("2d", { willReadFrequently: true });
  context.drawImage(video, 0, 0);
  const frame = context.getImageData(0, 0, canvas.width, canvas.height);
  return jsQR(frame.data, frame.width, frame.height)?.data ?? null;
}

async function sendScan(quiet) {
  if (inFlight || !stream || !el("video").videoWidth) return;
  inFlight = true;
  try {
    const id = readCode();
    if (!id) {
      if (!quiet) toast("No code in this frame");
      return;
    }
    const response = await fetch(`${SERVER}/captures`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    if (!response.ok) {
      const reason = refusal(await response.json());
      el("scan-state").textContent = `refused: ${reason}`;
      if (!quiet) toast(reason);
      return;
    }
    const entry = await response.json();
    el("scan-state").textContent = `paired ${entry.id}`;
    stopCamera();
    toast(`Paired ${entry.id}`);
    goto("pairs");
  } catch {
    el("scan-state").textContent = "server unreachable";
    if (!quiet) toast("Server unreachable");
  } finally {
    inFlight = false;
  }
}

async function loadPairs() {
  let entries = [];
  try {
    entries = await (await fetch(`${SERVER}/pairs`)).json();
  } catch {
    toast("Server unreachable");
    return;
  }
  el("pair-list").innerHTML = entries
    .map(
      (entry) => `
      <div class="pair">
        <div>
          <div class="mono">${entry.id}</div>
          <div class="tag">${entry.captured ? "captured" : "not captured yet"}</div>
        </div>
        <img src="${SERVER}/originals/${entry.id}.png" alt="original" />
        <img src="${SERVER}/pages/${entry.id}.png" alt="page" />
      </div>`
    )
    .join("");
}

function openSearch() {
  const dialog = el("search");
  const input = el("search-input");
  input.value = "";
  renderSearch("");
  dialog.showModal();
  input.focus();
}

async function searchRows(query) {
  const rows = TABS.map((tab, index) => ({
    label: `Tab ${index + 1} · ${tab}`,
    key: `⌘ ${index + 1}`,
    go: () => goto(tab),
  }));
  try {
    const entries = await (await fetch(`${SERVER}/pairs`)).json();
    entries.forEach((entry) =>
      rows.push({
        label: entry.id,
        key: entry.captured ? "captured" : "page only",
        go: () => {
          showPage(entry);
          goto("page");
        },
      })
    );
  } catch {}
  const needle = query.toLowerCase();
  return rows.filter((row) => row.label.toLowerCase().includes(needle));
}

let searchHits = [];
let searchIndex = 0;

async function renderSearch(query) {
  searchHits = await searchRows(query);
  searchIndex = 0;
  el("search-list").innerHTML = searchHits
    .map(
      (row, index) =>
        `<li class="${index === 0 ? "on" : ""}" data-index="${index}">
          <span>${row.label}</span><span class="key">${row.key}</span>
        </li>`
    )
    .join("");
}

function moveSearch(step) {
  const items = [...el("search-list").children];
  if (!items.length) return;
  items[searchIndex].classList.remove("on");
  searchIndex = (searchIndex + step + items.length) % items.length;
  items[searchIndex].classList.add("on");
  items[searchIndex].scrollIntoView({ block: "nearest" });
}

el("shortcut-list").innerHTML = SHORTCUTS.map(
  ([label, key]) => `<li><span>${label}</span><span class="key">${key}</span></li>`
).join("");

document.querySelectorAll("nav button").forEach((button) =>
  button.addEventListener("click", () => goto(button.dataset.tab))
);

el("drop").addEventListener("click", () => el("file").click());
el("file").addEventListener("change", (event) => {
  if (event.target.files[0]) upload(event.target.files[0]);
});
["dragover", "dragleave", "drop"].forEach((name) =>
  el("drop").addEventListener(name, (event) => {
    event.preventDefault();
    el("drop").classList.toggle("over", name === "dragover");
    if (name === "drop" && event.dataTransfer.files[0]) upload(event.dataTransfer.files[0]);
  })
);

el("go-page").addEventListener("click", () => goto("page"));
el("go-scan").addEventListener("click", () => goto("scan"));
el("refresh").addEventListener("click", loadPairs);
el("print").addEventListener("click", () => {
  if (!current) return toast("Upload an image first");
  window.desktop.printPage();
});
el("save").addEventListener("click", async () => {
  if (!current) return toast("Upload an image first");
  const bytes = await (await fetch(`${SERVER}/pages/${current.id}.png`)).arrayBuffer();
  const saved = await window.desktop.savePage(`${current.id}.png`, [...new Uint8Array(bytes)]);
  if (saved.ok) toast(`Saved to ${saved.path}`);
});
el("scan-toggle").addEventListener("click", () => (stream ? stopCamera() : startCamera()));
el("shoot").addEventListener("click", () => sendScan(false));

el("search-input").addEventListener("input", (event) => renderSearch(event.target.value));
el("search").addEventListener("keydown", (event) => {
  if (event.key === "ArrowDown") { event.preventDefault(); moveSearch(1); }
  if (event.key === "ArrowUp") { event.preventDefault(); moveSearch(-1); }
  if (event.key === "Enter") {
    event.preventDefault();
    el("search").close();
    searchHits[searchIndex]?.go();
  }
});
el("search-list").addEventListener("click", (event) => {
  const item = event.target.closest("li");
  if (!item) return;
  el("search").close();
  searchHits[Number(item.dataset.index)].go();
});

window.desktop.on("goto-tab", goto);
window.desktop.on("open-search", openSearch);
window.desktop.on("open-shortcuts", () => el("shortcuts").showModal());
window.desktop.on("toast", toast);

serverHealth();
setInterval(serverHealth, 5000);
