import React, { useState } from 'react';
import { Search, Bell, BellOff, ChevronRight, Activity } from 'lucide-react';

const MOCK_WALLETS = [
  { id: 1, alias: 'Solana Whale #2', address: '0x71c...a4', pnl: '+142.5%', network: 'SOL', isPositive: true, push: true, public_slug: 'crypto-wizard' },
  { id: 2, alias: 'Base Degen Alpha', address: '0x88b...1f', pnl: '-12.4%', network: 'BASE', isPositive: false, push: false, public_slug: 'whale-tracker' },
  { id: 3, alias: 'TON Market Maker', address: 'EQ_19...z8', pnl: '+34.2%', network: 'TON', isPositive: true, push: true, public_slug: 'sniper-bot' }
];

interface RadarProps {
  onTraderSelect?: (slug: string) => void;
}

export const Radar: React.FC<RadarProps> = ({ onTraderSelect }) => {
  const [wallets, setWallets] = useState(MOCK_WALLETS);
  const [selectedWallet, setSelectedWallet] = useState<number | null>(null);
  const [activeCategory, setActiveCategory] = useState('All');

  const togglePush = (id: number) => {
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
    }
    setWallets(wallets.map(w => w.id === id ? { ...w, push: !w.push } : w));
  };

  return (
    <div className="animate-fade-in flex flex-col gap-4">
      <div className="flex items-center justify-between mb-2">
        <h2>Smart Money Radar</h2>
      </div>

      <div className="relative">
        <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
          <Search size={18} className="text-hint" />
        </div>
        <input 
          type="text" 
          className="input-glass pl-10" 
          placeholder="Paste TON, SOL, or Base address..." 
        />
        <button className="absolute inset-y-1 right-1 btn-primary w-auto px-4 py-1 text-sm rounded-lg">
          Add
        </button>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide hide-scrollbars">
        {['All', 'Meme', 'Bluechip', 'Degen', 'Volume'].map(cat => (
          <button 
            key={cat} 
            className={`px-3 py-1.5 text-xs font-semibold rounded-full whitespace-nowrap transition-colors ${
              activeCategory === cat 
                ? 'bg-[var(--accent-blue)] text-white' 
                : 'bg-white/5 border border-white/10 text-hint hover:text-white'
            }`}
            onClick={() => setActiveCategory(cat)}
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="bg-gradient-to-r from-blue-600/20 to-purple-500/20 border border-[var(--accent-blue)]/30 rounded-xl p-3 flex justify-between items-center mt-1">
        <div>
          <h4 className="text-sm font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">ProofNode Premium</h4>
          <p className="text-xs text-white/70">Unlimited wallets & instant alerts</p>
        </div>
        <button className="px-3 py-1.5 bg-[var(--accent-blue)] text-white text-xs font-bold rounded-lg shadow-lg shadow-blue-500/20">
          Upgrade
        </button>
      </div>

      <div className="flex flex-col gap-3 mt-1">
        {wallets.map((wallet) => (
          <div key={wallet.id} className="glass-card flex flex-col gap-3" onClick={() => setSelectedWallet(wallet.id)}>
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  {wallet.alias}
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/10 text-white/70">
                    {wallet.network}
                  </span>
                </h3>
                <span className="text-hint font-mono text-sm">{wallet.address}</span>
              </div>
              <div className="flex flex-col items-end">
                <span className={`text-lg font-bold ${wallet.isPositive ? 'text-profit' : 'text-loss'}`}>
                  {wallet.pnl}
                </span>
                <span className="text-hint text-xs">30d ROI</span>
              </div>
            </div>
            
            <div className="flex items-center justify-between pt-2 border-t border-[var(--glass-border)]">
              <div className="flex items-center gap-2">
                {wallet.push ? <Bell size={16} className="text-[var(--accent-blue)]" /> : <BellOff size={16} className="text-hint" />}
                <span className="text-sm">Alerts</span>
                <label className="switch ml-2" onClick={(e) => e.stopPropagation()}>
                  <input type="checkbox" checked={wallet.push} onChange={() => togglePush(wallet.id)} />
                  <span className="slider"></span>
                </label>
              </div>
              
              <div 
                className="flex items-center text-hint text-sm gap-1 hover:text-white transition-colors cursor-pointer"
                onClick={(e) => {
                  e.stopPropagation();
                  if (onTraderSelect && wallet.public_slug) {
                    onTraderSelect(wallet.public_slug);
                  }
                }}
              >
                <span>View Details</span>
                <ChevronRight size={16} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {selectedWallet !== null && (
        <div className="fixed inset-0 z-50 flex items-end justify-center" style={{ background: 'rgba(0,0,0,0.6)' }} onClick={() => setSelectedWallet(null)}>
          <div className="w-full max-w-md bg-[var(--secondary-bg)] rounded-t-2xl p-6 shadow-2xl animate-fade-in border-t border-[var(--glass-border)]" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold">Recent Transactions</h3>
              <button className="text-hint" onClick={() => setSelectedWallet(null)}>Close</button>
            </div>
            <div className="flex flex-col gap-3">
              <div className="flex justify-between items-center bg-black/20 p-3 rounded-xl border border-[var(--glass-border)]">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-[var(--accent-green)]/20 flex items-center justify-center text-[var(--accent-green)]">
                    <Activity size={20} />
                  </div>
                  <div>
                    <div className="font-semibold">BUY $DOGE</div>
                    <div className="text-xs text-hint">2 mins ago • DEX: Ston.fi</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono font-bold text-[var(--accent-green)]">+500.0</div>
                  <div className="text-xs text-hint">-10.5 TON</div>
                </div>
              </div>
              <button className="btn-primary mt-2">
                <Activity size={18} />
                Copy Trade (1-Click)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
