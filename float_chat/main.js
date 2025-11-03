const { app, BrowserWindow, Menu, ipcMain, shell, screen } = require('electron');
const path = require('path');
const Store = require('electron-store');

// 创建配置存储
const store = new Store();

let mainWindow;

function createWindow() {
  // 获取屏幕尺寸
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize;

  // 计算默认窗口尺寸（屏幕宽度的四分之一，更紧凑）
  const defaultWidth = Math.floor(screenWidth / 4); // 改为1/4，约320px
  const defaultHeight = Math.floor(screenHeight * 0.75); // 高度调整为75%

  // 获取保存的窗口状态，如果没有则使用默认值
  const windowState = store.get('windowState', {
    width: defaultWidth,
    height: defaultHeight,
    x: screenWidth - defaultWidth - 50, // 默认位置在右侧，留50px边距
    y: Math.floor((screenHeight - defaultHeight) / 2) // 垂直居中
  });

  // 创建浏览器窗口
  mainWindow = new BrowserWindow({
    width: windowState.width,
    height: windowState.height,
    x: windowState.x,
    y: windowState.y,
    minWidth: 400, // 最小宽度调整为400px，适合聊天界面
    minHeight: 500, // 最小高度调整为500px
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets', 'luban.ico'),
    title: '小鲁AI',
    show: false, // 先不显示，等加载完成后再显示
    titleBarStyle: 'default',
    frame: true,
    alwaysOnTop: false, // 可以设置为true让窗口始终置顶
    resizable: true
  });

  // 加载应用
  mainWindow.loadFile('index.html');

  // 窗口准备好后显示
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();

    // 开发模式下打开开发者工具
    if (process.argv.includes('--dev')) {
      mainWindow.webContents.openDevTools();
    }
  });

  // 保存窗口状态
  mainWindow.on('close', () => {
    const bounds = mainWindow.getBounds();
    store.set('windowState', bounds);
  });

  // 处理窗口关闭
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // 处理外部链接
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // 阻止导航到外部页面
  mainWindow.webContents.on('will-navigate', (event, navigationUrl) => {
    const parsedUrl = new URL(navigationUrl);

    if (parsedUrl.origin !== 'file://') {
      event.preventDefault();
      shell.openExternal(navigationUrl);
    }
  });
}

// 应用准备就绪时创建窗口
app.whenReady().then(() => {
  createWindow();

  // 在 macOS 上，当点击 dock 图标且没有其他窗口打开时，重新创建窗口
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });

  // 设置应用菜单
  createMenu();
});

// 当所有窗口都关闭时退出应用（除了 macOS）
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// 创建应用菜单
function createMenu() {
  // 设置为null来隐藏菜单栏
  Menu.setApplicationMenu(null);
}

// IPC 处理程序
ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

ipcMain.handle('get-store-value', (event, key, defaultValue) => {
  return store.get(key, defaultValue);
});

ipcMain.handle('set-store-value', (event, key, value) => {
  store.set(key, value);
});

ipcMain.handle('delete-store-value', (event, key) => {
  store.delete(key);
});
