import { useState, useEffect } from 'react';
import { TRANSLATIONS } from './translations';
import type { Lang } from './translations';
import { TonConnectUIProvider } from '@tonconnect/ui-react';
import { initMockTelegram } from './utils/mockTelegram';
import { Toaster } from './components/ui/Toaster';
import { Navigation } from './components/Navigation';
import type { Tab } from './components/Navigation';
import Radar from './components/Radar';
import Leaderboard from './components/Leaderboard';
import Cabinet from './components/Cabinet';
import TraderProfile from './components/TraderProfile';
import { Languages } from 'lucide-react';

// Ensure mock telegram is initialized if running outside TMA
initMockTelegram();

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('radar');
  const [selectedTraderSlug, setSelectedTraderSlug] = useState<string | null>(null);
  const [walletConnected, setWalletConnected] = useState<boolean>(true);
  const [lang, setLang] = useState<Lang>(() => {
    const savedLang = localStorage.getItem('proofnode_lang') as Lang;
    return savedLang || 'ru';
  });

  useEffect(() => {
    // Tell Telegram WebApp we are ready
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
      
      // Enforce custom branding colors in the Telegram Mini App frame
      try {
        if (window.Telegram.WebApp.setHeaderColor) {
          window.Telegram.WebApp.setHeaderColor('#020617');
        }
        if (window.Telegram.WebApp.setBackgroundColor) {
          window.Telegram.WebApp.setBackgroundColor('#020617');
        }
      } catch (e) {
        console.error("Failed to enforce Telegram theme colors", e);
      }
      
      const startParam = window.Telegram.WebApp.initDataUnsafe?.start_param;
      if (startParam) {
        if (startParam.startsWith('copy_')) {
          setActiveTab('cabinet');
        } else if (startParam.startsWith('trader_')) {
          setActiveTab('radar');
        }
      }
    }
  }, []);

  const handleLangToggle = () => {
    const nextLang: Lang = lang === 'en' ? 'ru' : 'en';
    setLang(nextLang);
    localStorage.setItem('proofnode_lang', nextLang);
  };

  const handleConnectWalletToggle = () => {
    if ((window as any).Telegram?.WebApp?.HapticFeedback) {
      (window as any).Telegram.WebApp.HapticFeedback.impactOccurred('medium');
    }
    setWalletConnected(prev => !prev);
  };

  const t = TRANSLATIONS[lang];

  return (
    <TonConnectUIProvider manifestUrl="https://raw.githubusercontent.com/ton-community/tutorials/main/03-client/test/public/tonconnect-manifest.json">
      {/* Fixed Isolated Background Mesh Gradients to prevent horizontal scrolling */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-[-100px] left-[-100px] w-[500px] h-[500px] bg-sky-500/15 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[-50px] right-[-50px] w-[400px] h-[400px] bg-fuchsia-600/10 rounded-full blur-[100px]"></div>
        <div className="absolute top-[200px] right-[100px] w-[300px] h-[300px] bg-blue-500/10 rounded-full blur-[80px]"></div>
      </div>

      <div className="app-container text-slate-100 font-sans select-none antialiased">

        {/* Mini App Simulated Top Header */}
        <header className="bg-white/5 sticky top-0 z-50 border-b border-white/10 p-3 text-xs flex justify-between items-center backdrop-blur-md">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-sky-400 to-blue-600 flex items-center justify-center font-bold text-[10px] text-white shadow-lg">
              PN
            </div>
            <div>
              <span className="font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-blue-400">ProofNode</span>
              <span className="text-white/20 mx-1">|</span>
              <span className="text-white/60">Simulator</span>
            </div>
          </div>

          {/* Global Controls */}
          <div className="flex items-center gap-3">
            {/* Language Switch */}
            <button
              onClick={handleLangToggle}
              className="flex items-center gap-1.5 py-1 px-2.5 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 text-white/90 active:scale-95 transition-all cursor-pointer font-semibold"
            >
              <Languages size={12} className="text-sky-400" />
              <span>{lang.toUpperCase()}</span>
            </button>

            {/* Connection state short display */}
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${walletConnected ? 'bg-emerald-500' : 'bg-rose-500'} animate-pulse`} />
              <span className="text-[10px] text-white/40 font-mono">
                {walletConnected ? 'Live' : 'Disconnected'}
              </span>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 w-full p-4 overflow-y-auto">
          {selectedTraderSlug ? (
            <TraderProfile
              slug={selectedTraderSlug}
              onBack={() => setSelectedTraderSlug(null)}
            />
          ) : (
            <>
              {activeTab === 'radar' && (
                <Radar onTraderSelect={setSelectedTraderSlug} />
              )}
              {activeTab === 'leaderboard' && (
                <Leaderboard
                  onTraderSelect={setSelectedTraderSlug}
                  walletConnected={walletConnected}
                  onConnectWalletToggle={handleConnectWalletToggle}
                />
              )}
              {activeTab === 'cabinet' && (
                <Cabinet
                  walletConnected={walletConnected}
                  onConnectWalletToggle={handleConnectWalletToggle}
                />
              )}
            </>
          )}
        </main>

        <Navigation
          activeTab={activeTab}
          setActiveTab={(tab) => {
            setActiveTab(tab);
            setSelectedTraderSlug(null);
          }}
          selectedTraderSlug={selectedTraderSlug}
          t={t}
        />
        <Toaster />
      </div>
    </TonConnectUIProvider>
  );
}
