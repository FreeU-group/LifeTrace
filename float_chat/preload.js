const { contextBridge, ipcRenderer } = require('electron');

// 向渲染进程暴露安全的 API
contextBridge.exposeInMainWorld('electronAPI', {
  // 应用信息
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),

  // 存储相关
  getStoreValue: (key, defaultValue) => ipcRenderer.invoke('get-store-value', key, defaultValue),
  setStoreValue: (key, value) => ipcRenderer.invoke('set-store-value', key, value),
  deleteStoreValue: (key) => ipcRenderer.invoke('delete-store-value', key),

  // 监听主进程消息
  onNewChat: (callback) => {
    ipcRenderer.on('new-chat', callback);
  },

  // 移除监听器
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  }
});

// 在页面加载完成后注入一些全局变量
window.addEventListener('DOMContentLoaded', () => {
  // 标记这是 Electron 环境
  window.isElectron = true;

  // 设置应用标题
  document.title = '小鲁AI';
});
