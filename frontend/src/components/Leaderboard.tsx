import React, { useState } from 'react';
import type { Trader } from '../types';
import { INITIAL_TRADERS } from '../data';
import { Award, CheckCircle, Coins, Trophy, Sparkles } from 'lucide-react';

interface ArenaProps {
  onTraderSelect: (slug: string) => void;
  walletConnected: boolean;
  onConnectWalletToggle: () => void;
}

export default function ArenaView({ onTraderSelect, walletConnected, onConnectWalletToggle }: ArenaProps) {
  const [traders] = useState<Trader[]>(INITIAL_TRADERS);
  const [filter, setFilter] = useState<'All' | 'TON' | 'SOL' | 'BASE' | 'High Winrate'>('All');
  const [subscriptionTarget, setSubscriptionTarget] = useState<Trader | null>(null);
  const [checkoutStep, setCheckoutStep] = useState<'details' | 'success'>('details');

  const handleSubscribeClick = (e: React.MouseEvent, trader: Trader) => {
    e.stopPropagation();
    if (!walletConnected) {
      if ((window as any).Telegram?.WebApp?.HapticFeedback) {
        (window as any).Telegram.WebApp.HapticFeedback.notificationOccurred('warning');
      }
      onConnectWalletToggle();
      return;
    }
    setSubscriptionTarget(trader);
    setCheckoutStep('details');
  };

  const handleConfirmPay = () => {
    if ((window as any).Telegram?.WebApp?.HapticFeedback) {
      (window as any).Telegram.WebApp.HapticFeedback.notificationOccurred('success');
    }
    setCheckoutStep('success');
  };

  // Filter logic
  const filteredTraders = traders.filter(t => {
    if (filter === 'All') return true;
    if (filter === 'High Winrate') {
      return parseFloat(t.winrate.replace('%', '')) >= 80;
    }
    return t.blockchain === filter;
  });

  // SVG Sparkline Polyline generator
  const getSparklinePath = (data: number[]) => {
    if (data.length < 2) return '';
    const width = 100;
    const height = 30;
    const minVal = Math.min(...data);
    const maxVal = Math.max(...data);
    const spread = maxVal - minVal || 1;

    return data
      .map((val, idx) => {
        const x = (idx / (data.length - 1)) * width;
        const y = height - ((val - minVal) / spread) * height;
        return `${idx === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
      })
      .join(' ');
  };

  return (
    <div className="animate-fade-in flex flex-col gap-4">
      {/* Tab Header bar */}
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-xl font-bold flex items-center gap-2 text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-200">
          <Trophy className="text-amber-400 animate-pulse" size={20} />
          The Arena
        </h2>
        
        {/* TonConnect mock toggle */}
        <button
          onClick={onConnectWalletToggle}
          className={`text-xs py-1.5 px-3 rounded-full font-bold transition-all border ${
            walletConnected
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
              : 'bg-sky-500 hover:bg-sky-400 border-transparent text-white shadow-lg shadow-sky-500/25 active:scale-95'
          }`}
        >
          {walletConnected ? '✓ Connected' : 'Connect Wallet'}
        </button>
      </div>

      {/* Main hero card */}
      <div className="glass-card relative overflow-hidden mb-2">
        <div className="absolute top-0 right-0 p-4 opacity-5 text-sky-400">
          <Trophy size={64} />
        </div>
        <h3 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
          <Sparkles className="text-amber-400" size={16} />
          Proof-of-Trade Verification
        </h3>
        <p className="text-slate-300 text-xs mb-1">
          All P&L, ROI, and Winrates are audited and locked directly in-memory from blockchain trace decoders. Zero manual input.
        </p>
      </div>

      {/* Category filters */}
      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide hide-scrollbars">
        {(['All', 'TON', 'SOL', 'BASE', 'High Winrate'] as const).map(tab => (
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

      {/* Traders List */}
      <div className="flex flex-col gap-3">
        {filteredTraders.map((t, idx) => (
          <div
            key={t.id}
            className="glass-card flex flex-col gap-3 relative cursor-pointer hover:bg-white/[0.04] transition-all group"
            onClick={() => onTraderSelect(t.public_slug)}
          >
            {/* Header info */}
            <div className="flex justify-between items-start">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-black/40 flex items-center justify-center font-bold text-sm border border-white/10 text-amber-400 shadow-inner">
                  #{idx + 1}
                </div>
                <div>
                  <h3 className="text-base font-bold text-white flex items-center gap-1.5 leading-tight">
                    {t.name}
                    {t.is_verified && (
                      <CheckCircle size={14} className="text-[var(--accent-blue)] fill-[var(--accent-blue)]/10" />
                    )}
                    {t.badge === 'Elite' && (
                      <Award size={14} className="text-yellow-400" />
                    )}
                  </h3>
                  <span className="text-[10px] uppercase font-bold text-white/50 tracking-wider">
                    {t.blockchain} • {t.followers} Subscribers
                  </span>
                </div>
              </div>

              <div className="text-right">
                <span className="text-lg font-black text-profit block leading-none">
                  {t.roi}
                </span>
                <span className="text-hint text-[10px]">Winrate: {t.winrate}</span>
              </div>
            </div>

            {/* Sparkline Graph */}
            <div className="w-full h-10 mt-1 relative">
              <svg viewBox="0 0 100 30" className="w-full h-full" preserveAspectRatio="none">
                <path
                  d={getSparklinePath(t.chartData)}
                  fill="none"
                  stroke="var(--accent-green)"
                  strokeWidth="2"
                  vectorEffect="non-scaling-stroke"
                />
                <path
                  d={`${getSparklinePath(t.chartData)} L 100 30 L 0 30 Z`}
                  fill="url(#sparklineGrad)"
                  opacity="0.1"
                />
                <defs>
                  <linearGradient id="sparklineGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="var(--accent-green)" stopOpacity="1" />
                    <stop offset="100%" stopColor="var(--accent-green)" stopOpacity="0" />
                  </linearGradient>
                </defs>
              </svg>
            </div>

            {/* Actions */}
            <div className="flex justify-between items-center pt-2 border-t border-white/[0.06] mt-1">
              <div className="text-xs text-hint">
                Monthly Subscription: <span className="font-bold text-white">{t.price}</span>
              </div>
              <button
                onClick={(e) => handleSubscribeClick(e, t)}
                className="btn-primary w-auto py-1.5 px-4 text-xs font-bold rounded-lg"
              >
                Subscribe
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Subscription Paywall Modal Drawer */}
      {subscriptionTarget && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/75 backdrop-blur-md transition-opacity duration-300"
          onClick={() => setSubscriptionTarget(null)}
        >
          <div
            className="w-full max-w-md bg-slate-950/80 backdrop-blur-2xl rounded-t-3xl p-6 shadow-2xl border-t border-white/10 animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Grabber bar */}
            <div className="w-12 h-1.5 bg-white/20 rounded-full mx-auto mb-5 cursor-pointer" onClick={() => setSubscriptionTarget(null)} />
            
            {checkoutStep === 'details' ? (
              <div className="flex flex-col gap-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-xl font-bold flex items-center gap-2 text-white">
                      <Award size={20} className="text-amber-400" />
                      Subscribe to {subscriptionTarget.name}
                    </h3>
                    <p className="text-slate-400 text-xs mt-1">
                      Platform copy fee split: 5% treasury commission / 95% trader payout.
                    </p>
                  </div>
                  <button
                    className="text-slate-400 hover:text-white text-sm"
                    onClick={() => setSubscriptionTarget(null)}
                  >
                    Cancel
                  </button>
                </div>

                <div className="bg-black/30 p-4 rounded-2xl border border-white/5 flex flex-col gap-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Subscription Period:</span>
                    <span className="font-semibold text-white">30 Days (Automatic Renew)</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Total Price:</span>
                    <span className="font-bold text-sky-400">{subscriptionTarget.price}</span>
                  </div>
                  <div className="flex justify-between text-sm border-t border-white/[0.05] pt-3">
                    <span className="text-slate-400">DEX Execution Route:</span>
                    <span className="text-xs font-mono text-white/50">{subscriptionTarget.blockchain} Aggregator</span>
                  </div>
                </div>

                <p className="text-xs text-slate-400 leading-relaxed">
                  Upon confirming, you authorize automated transaction copying when private webhook swaps are triggered. You can change allocation thresholds at any time in the Cabinet.
                </p>

                <button
                  className="btn-primary w-full py-4 mt-2 font-bold flex items-center justify-center gap-2 shadow-lg shadow-sky-500/25"
                  onClick={handleConfirmPay}
                >
                  <Coins size={18} />
                  Confirm & Transfer Payout
                </button>
              </div>
            ) : (
              <div className="flex flex-col gap-4 text-center py-4">
                <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-2 text-emerald-400 animate-pulse">
                  <Trophy size={32} />
                </div>
                <h3 className="text-xl font-bold text-white">Subscription Verified!</h3>
                <p className="text-sm text-slate-300 max-w-xs mx-auto">
                  You have successfully unlocked 30-day signal tracking and automated cloud copying.
                </p>
                <div className="p-3 bg-black/40 rounded-xl font-mono text-xs text-center border border-white/10 break-all select-all">
                  t.me/AlphaHubBot/join_group_token
                </div>
                <p className="text-xs text-slate-400">Copy invitation code to rejoin official chat.</p>
                <button
                  className="btn-secondary w-full py-3 mt-4"
                  onClick={() => setSubscriptionTarget(null)}
                >
                  Close Checkout
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
