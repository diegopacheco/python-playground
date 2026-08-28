const node = document.getElementById("flash");
let timer = null;

export function flash(message, kind = "ok") {
  node.textContent = message;
  node.className = `flash ${kind}`;
  node.hidden = false;
  clearTimeout(timer);
  timer = setTimeout(() => {
    node.hidden = true;
  }, 4000);
}
