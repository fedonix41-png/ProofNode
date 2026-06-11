// Mock Telegram WebApp for local development outside Telegram
export const initMockTelegram = () => {
  if (typeof window !== 'undefined' && !window.Telegram) {
    console.log('Initializing Mock Telegram WebApp SDK');
    window.Telegram = {
      WebApp: {
        initData: "query_id=mock_query_id&user=%7B%22id%22%3A123456789%2C%22first_name%22%3A%22Alpha%22%2C%22last_name%22%3A%22User%22%2C%22username%22%3A%22alpha_user%22%2C%22language_code%22%3A%22en%22%7D&auth_date=1672531200&hash=mock_hash",
        initDataUnsafe: {
          query_id: "mock_query_id",
          user: {
            id: 123456789,
            first_name: "Alpha",
            last_name: "User",
            username: "alpha_user",
            language_code: "en"
          },
          auth_date: 1672531200,
          hash: "mock_hash"
        },
        version: "6.0",
        platform: "unknown",
        colorScheme: "dark",
        themeParams: {
          bg_color: "#121214",
          text_color: "#ffffff",
          hint_color: "#8a8a93",
          link_color: "#00a2ff",
          button_color: "#00a2ff",
          button_text_color: "#ffffff",
          secondary_bg_color: "#1a1a1e"
        },
        isExpanded: true,
        viewportHeight: window.innerHeight,
        viewportStableHeight: window.innerHeight,
        headerColor: "#121214",
        backgroundColor: "#121214",
        isClosingConfirmationEnabled: false,
        BackButton: {
          isVisible: false,
          show: () => { console.log('Mock: BackButton.show()'); },
          hide: () => { console.log('Mock: BackButton.hide()'); },
          onClick: (cb: () => void) => { console.log('Mock: BackButton.onClick()'); }
        },
        MainButton: {
          text: "CONTINUE",
          color: "#00a2ff",
          textColor: "#ffffff",
          isVisible: false,
          isActive: true,
          isProgressVisible: false,
          setText: (text: string) => { console.log(`Mock: MainButton.setText(${text})`); },
          onClick: (cb: () => void) => { console.log('Mock: MainButton.onClick()'); },
          show: () => { console.log('Mock: MainButton.show()'); },
          hide: () => { console.log('Mock: MainButton.hide()'); },
          enable: () => { console.log('Mock: MainButton.enable()'); },
          disable: () => { console.log('Mock: MainButton.disable()'); },
          showProgress: (leaveActive: boolean) => { console.log(`Mock: MainButton.showProgress(${leaveActive})`); },
          hideProgress: () => { console.log('Mock: MainButton.hideProgress()'); },
          setParams: (params: any) => { console.log('Mock: MainButton.setParams()', params); }
        },
        HapticFeedback: {
          impactOccurred: (style: string) => { console.log(`Mock: Haptic.impact(${style})`); },
          notificationOccurred: (type: string) => { console.log(`Mock: Haptic.notification(${type})`); },
          selectionChanged: () => { console.log('Mock: Haptic.selection()'); }
        },
        ready: () => { console.log('Mock: WebApp.ready()'); },
        expand: () => { console.log('Mock: WebApp.expand()'); },
        close: () => { console.log('Mock: WebApp.close()'); }
      }
    };
  }
};

// Global augmentation
declare global {
  interface Window {
    Telegram?: {
      WebApp: any;
    };
  }
}
