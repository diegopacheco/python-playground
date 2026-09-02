const { app, BrowserWindow, Menu, dialog, ipcMain, shell, systemPreferences } = require("electron");
const fs = require("fs");
const path = require("path");
const os = require("os");

const STATE_FILE = path.join(app.getPath("userData"), "window-state.json");
const DEFAULT_STATE = { width: 1180, height: 840, fullScreen: false };

let win = null;

function readState() {
  try {
    return { ...DEFAULT_STATE, ...JSON.parse(fs.readFileSync(STATE_FILE, "utf8")) };
  } catch {
    return { ...DEFAULT_STATE };
  }
}

function saveState() {
  if (!win || win.isDestroyed()) return;
  const fullScreen = win.isFullScreen();
  const bounds = fullScreen ? readState() : win.getNormalBounds();
  const state = {
    x: bounds.x,
    y: bounds.y,
    width: bounds.width,
    height: bounds.height,
    fullScreen,
  };
  fs.writeFileSync(STATE_FILE, JSON.stringify(state));
}

function send(channel, payload) {
  if (win && !win.isDestroyed()) win.webContents.send(channel, payload);
}

function buildMenu() {
  const tabs = ["upload", "page", "scan", "pairs"].map((tab, index) => ({
    label: `Tab ${index + 1}`,
    accelerator: `CommandOrControl+${index + 1}`,
    click: () => send("goto-tab", tab),
  }));

  Menu.setApplicationMenu(
    Menu.buildFromTemplate([
      {
        role: "appMenu",
      },
      {
        label: "Edit",
        submenu: [
          { role: "undo" },
          { role: "redo" },
          { type: "separator" },
          { role: "cut" },
          { role: "copy" },
          { role: "paste" },
          { role: "selectAll" },
          { type: "separator" },
          {
            label: "Search",
            accelerator: "CommandOrControl+K",
            click: () => send("open-search"),
          },
        ],
      },
      {
        label: "View",
        submenu: [
          {
            label: "Zoom In",
            accelerator: "CommandOrControl+Plus",
            click: () => win.webContents.setZoomLevel(win.webContents.getZoomLevel() + 0.5),
          },
          {
            label: "Zoom In",
            accelerator: "CommandOrControl+=",
            visible: false,
            click: () => win.webContents.setZoomLevel(win.webContents.getZoomLevel() + 0.5),
          },
          {
            label: "Zoom Out",
            accelerator: "CommandOrControl+-",
            click: () => win.webContents.setZoomLevel(win.webContents.getZoomLevel() - 0.5),
          },
          { type: "separator" },
          ...tabs,
          { type: "separator" },
          {
            label: "Full Screen",
            accelerator: "CommandOrControl+Shift+Return",
            click: () => win.setFullScreen(!win.isFullScreen()),
          },
          {
            label: "Capture Screen",
            accelerator: "CommandOrControl+P",
            click: captureScreen,
          },
          { role: "reload" },
          { role: "toggleDevTools" },
        ],
      },
      {
        label: "Help",
        submenu: [
          {
            label: "Shortcuts",
            accelerator: "CommandOrControl+/",
            click: () => send("open-shortcuts"),
          },
        ],
      },
    ])
  );
}

async function captureScreen() {
  const image = await win.webContents.capturePage();
  const target = path.join(
    os.homedir(),
    "Desktop",
    `qr-page-capture-${Date.now()}.png`
  );
  fs.writeFileSync(target, image.toPNG());
  send("toast", `Screen capture saved to ${target}`);
  shell.showItemInFolder(target);
}

function createWindow() {
  const state = readState();
  win = new BrowserWindow({
    x: state.x,
    y: state.y,
    width: state.width,
    height: state.height,
    minWidth: 900,
    minHeight: 640,
    backgroundColor: "#faf9f7",
    titleBarStyle: "hiddenInset",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (state.fullScreen) win.setFullScreen(true);

  win.loadFile(path.join(__dirname, "index.html"));
  win.on("close", saveState);
  win.on("closed", () => {
    win = null;
  });
}

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (!win) return;
    if (win.isMinimized()) win.restore();
    win.focus();
  });

  app.whenReady().then(() => {
    buildMenu();
    createWindow();
    app.on("activate", () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  });

  app.on("window-all-closed", () => app.quit());
}

ipcMain.handle("ask-camera", async () => {
  if (process.platform !== "darwin") return true;
  return systemPreferences.askForMediaAccess("camera");
});

ipcMain.handle("print-page", async () => {
  return new Promise((resolve) => {
    win.webContents.print({ silent: false, printBackground: true }, (ok, reason) =>
      resolve({ ok, reason })
    );
  });
});

ipcMain.handle("save-page", async (_event, { name, bytes }) => {
  const chosen = await dialog.showSaveDialog(win, { defaultPath: name });
  if (chosen.canceled) return { ok: false };
  fs.writeFileSync(chosen.filePath, Buffer.from(bytes));
  return { ok: true, path: chosen.filePath };
});
