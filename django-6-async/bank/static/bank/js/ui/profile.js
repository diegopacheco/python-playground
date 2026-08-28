import { api } from "../api.js";
import { money, dateTime } from "../format.js";
import { reload, state } from "../store.js";
import { flash } from "./flash.js";

const picker = document.getElementById("profile-picker");
const form = document.getElementById("create-form");

const text = (id, value) => (document.getElementById(id).textContent = value);

export function mountProfile() {
  picker.addEventListener("change", () => reload(Number(picker.value)));

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    try {
      const profile = await api.createProfile(data.get("full_name"), data.get("email"));
      form.reset();
      await reload(profile.id);
      flash(`Account ${profile.account.number} opened for ${profile.full_name}`);
    } catch (error) {
      flash(error.message, "error");
    }
  });
}

export function renderProfile() {
  const { profiles, profile } = state;

  picker.innerHTML = profiles
    .map((p) => `<option value="${p.id}">${p.full_name}</option>`)
    .join("");
  picker.value = profile ? profile.id : "";
  picker.disabled = profiles.length === 0;

  text("card-owner", profile ? profile.full_name : "No profile yet");
  text("card-number", profile ? profile.account.number : "—");
  text("card-balance", profile ? profile.account.balance : "0.00");

  text("detail-name", profile ? profile.full_name : "—");
  text("detail-email", profile ? profile.email : "—");
  text("detail-number", profile ? profile.account.number : "—");
  text("detail-balance", profile ? money(profile.account.balance) : "—");
  text("detail-since", profile ? dateTime(profile.created_at) : "—");
}
