import { reload, subscribe } from "./store.js";
import { flash } from "./ui/flash.js";
import { renderHistory } from "./ui/history.js";
import { mountMoney, renderMoney } from "./ui/money.js";
import { mountProfile, renderProfile } from "./ui/profile.js";
import { mountTabs } from "./ui/tabs.js";

mountTabs();
mountProfile();
mountMoney();

subscribe(() => {
  renderProfile();
  renderMoney();
  renderHistory();
});

reload().catch((error) => flash(error.message, "error"));
