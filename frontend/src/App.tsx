import React, { useEffect, useState } from 'react';
import { TonConnectUIProvider } from '@tonconnect/ui-react';
import { Navigation } from './components/Navigation';
import type { Tab } from './components/Navigation';
import { Radar } from './components/Radar';
import { Leaderboard } from './components/Leaderboard';
import { Cabinet } from './components/Cabinet';
import { initMockTelegram } from './utils/mockTelegram';

// Ensure mock telegram is initialized if running outside TMA
initMockTelegram();

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('radar');

  useEffect(() => {
    // Tell Telegram WebApp we are ready
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
      
      // Apply theme bg explicitly to the body
      const bgColor = window.Telegram.WebApp.backgroundColor || window.Telegram.WebApp.themeParams?.bg_color;
      if (bgColor) {
        document.body.style.backgroundColor = bgColor;
      }
    }
  }, []);

  return (
    <TonConnectUIProvider manifestUrl="https://raw.githubusercontent.com/ton-community/tutorials/main/03-client/test/public/tonconnect-manifest.json">
      <div className="app-container">
        <main className="content-area">
          {activeTab === 'radar' && <Radar />}
          {activeTab === 'leaderboard' && <Leaderboard />}
          {activeTab === 'cabinet' && <Cabinet />}
        </main>
        
        <Navigation activeTab={activeTab} setActiveTab={setActiveTab} />
      </div>
    </TonConnectUIProvider>
  );
}

export default App;
