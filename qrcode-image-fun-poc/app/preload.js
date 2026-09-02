const { contextBridge, ipcRenderer } = require("electron");

const channels = ["goto-tab", "open-search", "open-shortcuts", "toast"];

contextBridge.exposeInMainWorld("desktop", {
  on: (channel, handler) => {
    if (!channels.includes(channel)) return;
    ipcRenderer.on(channel, (_event, payload) => handler(payload));
  },
  askCamera: () => ipcRenderer.invoke("ask-camera"),
  printPage: () => ipcRenderer.invoke("print-page"),
  savePage: (name, bytes) => ipcRenderer.invoke("save-page", { name, bytes }),
});
