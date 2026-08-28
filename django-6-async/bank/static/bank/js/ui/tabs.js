export function mountTabs() {
  const tabs = [...document.querySelectorAll(".tab")];
  const panes = [...document.querySelectorAll(".pane")];

  function select(name) {
    tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === name));
    panes.forEach((pane) => pane.classList.toggle("active", pane.dataset.pane === name));
  }

  tabs.forEach((tab) => tab.addEventListener("click", () => select(tab.dataset.tab)));
  select("profile");
}
