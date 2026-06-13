import React, { useState } from 'react';
import type { MonitoredWallet } from '../types';
import { INITIAL_MONITORED } from '../data';
import { Bell, BellOff, ChevronRight, Search, ShieldCheck, Zap } from 'lucide-react';

interface RadarProps {
  onTraderSelect: (slug: string) => void;
}

export default function RadarView({ onTraderSelect }: RadarProps) {
  const [wallets, setWallets] = useState<MonitoredWallet[]>(INITIAL_MONITORED);
  const [selectedWalletId, setSelectedWalletId] = useState<string | null>(null);
  const [filter, setFilter] = useState<'All' | 'TON' | 'SOL' | 'BASE'>('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  const handleToggleAlert = (id: string) => {
    // Attempt haptic feedback if available (simulated or real in Telegram WebApp)
    if ((window as any).Telegram?.WebApp?.HapticFeedback) {
      (window as any).Telegram.WebApp.HapticFeedback.impactOccurred('light');
    }
    
    setWallets(prev =>
      prev.map(w => (w.id === id ? { ...w, push: !w.push } : w))
    );
    showFeedback("Alert settings updated!");
  };

  const showFeedback = (msg: string) => {
    setFeedbackMsg(msg);
    setTimeout(() => setFeedbackMsg(null), 3500);
  };

  const handleAddWallet = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    // Detect network based on prefix
    let detectedChain: 'TON' | 'SOL' | 'BASE' = 'TON';
    const addr = searchQuery.trim();
    if (addr.startsWith('0x')) {
      detectedChain = 'BASE';
    } else if (addr.length > 40 && !addr.includes('_')) {
      detectedChain = 'SOL';
    }

    const newWallet: MonitoredWallet = {
      id: `mw_${Date.now()}`,
      address: addr.substring(0, 6) + '...' + addr.substring(addr.length - 4),
      blockchain: detectedChain,
      label: `Tracked Wallet #${wallets.length + 1}`,
      pnl: '+24.8%',
      isPositive: true,
      push: true,
      public_slug: detectedChain === 'TON' ? 'sniper-bot' : detectedChain === 'SOL' ? 'crypto-wizard' : 'whale-tracker'
    };

    setWallets(prev => [newWallet, ...prev]);
    setSearchQuery('');
    showFeedback(`Added ${detectedChain} wallet successfully!`);
    
    if ((window as any).Telegram?.WebApp?.HapticFeedback) {
      (window as any).Telegram.WebApp.HapticFeedback.notificationOccurred('success');
    }
  };

  const filteredWallets = wallets.filter(w => {
    if (filter === 'All') return true;
    return w.blockchain === filter;
  });

  return (
    <div className="animate-fade-in flex flex-col gap-4">
      {/* Title */}
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-xl font-bold flex items-center gap-2 text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-blue-400">
          <Zap className="text-sky-400 animate-pulse" size={20} />
          Smart Money Radar
        </h2>
        <span className="text-white/40 text-xs bg-white/5 py-1 px-3 rounded-full border border-white/10 font-mono">
          {wallets.length} active slots
        </span>
      </div>

      {/* Input box */}
      <form onSubmit={handleAddWallet} className="relative">
        <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
          <Search size={18} className="text-slate-400" />
        </div>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="input-glass w-full rounded-xl py-3 pl-10 pr-24 text-sm text-white focus:outline-none focus:ring-1 focus:ring-sky-500 placeholder:text-slate-400 font-sans transition-all"
          placeholder="Paste TON, SOL, or Base address..."
        />
        <button
          type="submit"
          className="absolute inset-y-1.5 right-1.5 bg-sky-500 hover:bg-sky-400 active:scale-95 text-slate-950 font-sans font-bold text-xs uppercase tracking-wider px-4 rounded-lg flex items-center justify-center transition-all shadow-lg shadow-sky-500/20 h-auto border-none cursor-pointer"
        >
          Add
        </button>
      </form>

      {/* Filter Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide hide-scrollbars">
        {(['All', 'TON', 'SOL', 'BASE'] as const).map(tab => (
          <button
            key={tab}
            className={`px-3 py-1.5 text-xs font-semibold rounded-full whitespace-nowrap transition-all ${
              filter === tab
                ? 'bg-sky-500 text-white shadow-lg shadow-sky-500/25'
                : 'bg-white/5 border border-white/10 text-slate-300 hover:text-white hover:bg-white/10'
            }`}
            onClick={() => setFilter(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Feedback Toast Notification */}
      {feedbackMsg && (
        <div className="fixed bottom-24 left-1/2 transform -translate-x-1/2 z-50 bg-[#0c1020] border border-white/10 text-white px-4 py-3 rounded-xl text-xs flex items-center gap-2 shadow-2xl animate-fade-in backdrop-blur-md">
          <ShieldCheck size={14} className="text-[var(--accent-green)]" />
          <span>{feedbackMsg}</span>
        </div>
      )}

      {/* Upgrade Callout */}
      <div className="bg-gradient-to-r from-sky-500/20 to-blue-500/20 border border-white/10 rounded-2xl p-4 flex justify-between items-center relative overflow-hidden">
        <div className="absolute top-0 right-0 w-24 h-24 bg-sky-500/10 blur-xl rounded-full" />
        <div>
          <h4 className="text-sm font-bold text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-blue-400">
            ProofNode Premium Active
          </h4>
          <p className="text-xs text-white/70">
            You have unlimited wallet monitoring & instant push triggers.
          </p>
        </div>
        <span className="text-[10px] bg-sky-500/20 text-sky-400 px-2 py-0.5 rounded font-mono border border-sky-500/30 font-bold">
          LIFETIME
        </span>
      </div>

      {/* Wallets List */}
      <div className="flex flex-col gap-3">
        {filteredWallets.length === 0 ? (
          <div className="text-center text-hint py-8 bg-white/[0.02] border border-white/[0.05] rounded-2xl">
            No wallets found under "{filter}".
          </div>
        ) : (
          filteredWallets.map(w => (
            <div
              key={w.id}
              className="glass-card hover:bg-white/[0.05] transition-all cursor-pointer flex flex-col gap-3 group relative overflow-hidden"
              onClick={() => setSelectedWalletId(w.id)}
            >
              {/* Glowing highlight indicator */}
              <div className={`absolute top-0 left-0 w-1 h-full bg-gradient-to-b ${
                w.blockchain === 'TON' ? 'from-sky-500 to-blue-600' :
                w.blockchain === 'SOL' ? 'from-purple-500 to-fuchsia-600' :
                'from-gray-500 to-slate-600'
              }`} />

              <div className="flex justify-between items-start pl-2">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      {w.label}
                    </h3>
                    <span className={`text-[10px] px-2 py-0.5 font-mono rounded-full font-bold border ${
                      w.blockchain === 'TON' ? 'bg-sky-500/10 text-sky-400 border-sky-500/20' :
                      w.blockchain === 'SOL' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' :
                      'bg-slate-500/10 text-slate-400 border-slate-500/20'
                    }`}>
                      {w.blockchain}
                    </span>
                  </div>
                  <span className="text-hint font-mono text-xs">{w.address}</span>
                </div>

                <div className="text-right">
                  <div className={`text-base font-black ${w.isPositive ? 'text-profit' : 'text-loss'}`}>
                    {w.pnl}
                  </div>
                  <span className="text-hint text-[10px] block">30d Net Profit</span>
                </div>
              </div>

              {/* Bot Alert and Navigation Row */}
              <div className="flex items-center justify-between pt-2 pl-2 border-t border-white/[0.06]">
                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleAlert(w.id);
                    }}
                    className={`p-2 rounded-lg border transition-all ${
                      w.push
                        ? 'bg-[var(--accent-blue)]/10 border-[var(--accent-blue)]/20 text-[var(--accent-blue)]'
                        : 'bg-white/5 border-white/10 text-hint hover:text-white'
                    }`}
                  >
                    {w.push ? <Bell size={14} className="animate-bounce" /> : <BellOff size={14} />}
                  </button>
                  <span className="text-xs text-white/80">
                    {w.push ? 'Push triggers active' : 'Alerts suspended'}
                  </span>
                </div>

                {w.public_slug && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onTraderSelect(w.public_slug!);
                    }}
                    className="flex items-center text-hint text-xs gap-1 hover:text-[var(--accent-blue)] transition-colors"
                  >
                    <span>View trader</span>
                    <ChevronRight size={14} />
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Selected Wallet Detail Bottom Drawer/Modal */}
      {selectedWalletId && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-sm"
          onClick={() => setSelectedWalletId(null)}
        >
          <div
            className="w-full max-w-md bg-[var(--secondary-bg)] rounded-t-3xl p-6 shadow-2xl border-t border-white/10 animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Handle bar */}
            <div className="w-12 h-1.5 bg-white/20 rounded-full mx-auto mb-4 cursor-pointer" onClick={() => setSelectedWalletId(null)} />
            
            {(() => {
              const sel = wallets.find(w => w.id === selectedWalletId);
              if (!sel) return null;
              return (
                <div className="flex flex-col gap-4">
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        {sel.label}
                        <span className="text-xs bg-white/10 text-white/80 px-2 py-0.5 rounded-full font-mono">
                          {sel.blockchain}
                        </span>
                      </h3>
                      <p className="text-hint text-xs font-mono">{sel.address}</p>
                    </div>
                    <button
                      className="text-hint hover:text-white text-sm"
                      onClick={() => setSelectedWalletId(null)}
                    >
                      Close
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-3 my-2">
                    <div className="flex flex-col bg-black/20 p-3 rounded-xl border border-white/5">
                      <span className="text-hint text-xs">Total Trades</span>
                      <span className="text-lg font-bold text-white">42</span>
                    </div>
                    <div className="flex flex-col bg-black/20 p-3 rounded-xl border border-white/5">
                      <span className="text-hint text-xs">Avg Slip Tolerance</span>
                      <span className="text-lg font-bold text-white">0.50%</span>
                    </div>
                  </div>

                  <div className="bg-black/30 p-4 rounded-xl border border-white/5">
                    <h4 className="text-xs font-bold text-hint mb-3">RECENT ACTIVITY LOG</h4>
                    <div className="flex flex-col gap-2.5">
                      <div className="flex justify-between items-center text-xs">
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-[var(--accent-green)]" />
                          <span className="text-white/90">BUY $SCALE</span>
                        </div>
                        <span className="text-hint">5m ago</span>
                      </div>
                      <div className="flex justify-between items-center text-xs">
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-[var(--accent-green)]" />
                          <span className="text-white/90">BUY $DOGE</span>
                        </div>
                        <span className="text-hint">12m ago</span>
                      </div>
                      <div className="flex justify-between items-center text-xs">
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-[var(--accent-red)]" />
                          <span className="text-white/90">SELL $USDT</span>
                        </div>
                        <span className="text-hint">1h ago</span>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      setSelectedWalletId(null);
                      if (sel.public_slug) onTraderSelect(sel.public_slug);
                    }}
                    className="btn-primary w-full py-3 mt-1"
                  >
                    <Zap size={16} />
                    Configure Automated Copy
                  </button>
                </div>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}
