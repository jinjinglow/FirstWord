const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("desktop", {
  platform: process.platform,
  apiBaseUrl: "http://127.0.0.1:8766"
});
