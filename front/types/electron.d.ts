declare global {
  interface Window {
    electronAPI: {
      getAppVersion: () => Promise<string>;
      getAppName: () => Promise<string>;
      minimizeToTray: () => Promise<void>;
      quitApp: () => Promise<void>;
      platform: string;
      isElectron: boolean;
    };
    versions: {
      node: string;
      chrome: string;
      electron: string;
    };
  }
}

export {};
