import { useEffect, useState } from 'react';
import { TonConnectUIProvider } from '@tonconnect/ui-react';
import { Navigation } from './components/Navigation';
import type { Tab } from './components/Navigation';
import { Radar } from './components/Radar';
import { Leaderboard } from './components/Leaderboard';
import { Cabinet } from './components/Cabinet';
import { TraderProfile } from './components/TraderProfile';
import { initMockTelegram } from './utils/mockTelegram';

// Ensure mock telegram is initialized if running outside TMA
initMockTelegram();

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('radar');
  const [selectedTraderSlug, setSelectedTraderSlug] = useState<string | null>(null);

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
      
      const startParam = window.Telegram.WebApp.initDataUnsafe?.start_param;
      if (startParam) {
        console.log("App opened with start param:", startParam);
        if (startParam.startsWith('ref_')) {
          // Track referral
          console.log("Referral link activated:", startParam);
          const userId = window.Telegram.WebApp.initDataUnsafe?.user?.id || 12345;
          fetch('/api/users/apply_referral', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, referral_code: startParam })
          }).catch(e => console.error("Failed to apply referral", e));
        } else if (startParam.startsWith('copy_')) {
          // Route to cabinet for copy trade setup
          setActiveTab('cabinet');
        } else if (startParam.startsWith('trader_')) {
          // Route to radar for trader view
          setActiveTab('radar');
        }
      }
    }
  }, []);

  return (
    <TonConnectUIProvider manifestUrl="https://raw.githubusercontent.com/ton-community/tutorials/main/03-client/test/public/tonconnect-manifest.json">
      <div className="app-container">
        <main className="content-area">
          {selectedTraderSlug ? (
            <TraderProfile 
              slug={selectedTraderSlug} 
              onBack={() => setSelectedTraderSlug(null)} 
            />
          ) : (
            <>
              {activeTab === 'radar' && <Radar onTraderSelect={setSelectedTraderSlug} />}
              {activeTab === 'leaderboard' && <Leaderboard onTraderSelect={setSelectedTraderSlug} />}
              {activeTab === 'cabinet' && <Cabinet />}
            </>
          )}
        </main>
        
        <Navigation 
          activeTab={activeTab} 
          setActiveTab={(tab) => {
            setActiveTab(tab);
            setSelectedTraderSlug(null);
          }} 
        />
      </div>
    </TonConnectUIProvider>
  );
}

export default App;
