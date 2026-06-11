import React, { useState } from 'react';
import { TonConnectButton, useTonConnectUI, useTonWallet } from '@tonconnect/ui-react';
import { Trophy, Star, ShieldCheck } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { generateSparklinePath } from '../utils/sparkline';
import { toast } from './ui/Toaster';
import { Skeleton } from './ui/Skeleton';

import { useTraderStore } from '../store/useTraderStore';

interface LeaderboardProps {
  onTraderSelect?: (slug: string) => void;
}

export const Leaderboard: React.FC<LeaderboardProps> = ({ onTraderSelect }) => {
  const [tonConnectUI] = useTonConnectUI();
  const wallet = useTonWallet();
  const { traders, isLoading, fetchTraders } = useTraderStore();
  const [activeFilter, setActiveFilter] = useState('All');

  React.useEffect(() => {
    const filters: any = {};
    if (['TON', 'SOL', 'BASE'].includes(activeFilter)) {
      filters.blockchain = activeFilter;
    } else if (activeFilter === 'High Winrate') {
      filters.high_winrate = true;
    }
    fetchTraders(filters);
  }, [activeFilter, fetchTraders]);

  const handleSubscribe = async (trader: any) => {
    if (!wallet) {
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred('warning');
      }
      toast('Please connect your TON wallet first', 'error');
      return;
    }

    if (trader.price === 'FREE') return;

    try {
      const amountInNano = parseInt(trader.price) * 1000000000;
      
      const transaction = {
        validUntil: Math.floor(Date.now() / 1000) + 60, // 60 sec
        messages: [
          {
            address: "EQ_MOCK_PLATFORM_ADDRESS_HERE", 
            amount: amountInNano.toString(),
            payload: "mock_subscription_payload"
          }
        ]
      };

      const result = await tonConnectUI.sendTransaction(transaction);
      
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred('success');
      }
      console.log('Transaction success:', result);
      toast(`Subscribed to ${trader.name}!`, 'success');

    } catch (e) {
      console.error(e);
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred('error');
      }
    }
  };

  return (
    <div className="animate-fade-in flex flex-col gap-4">
      <div className="flex items-center justify-between mb-2">
        <h2 className="flex items-center gap-2"><Trophy size={24} className="text-[var(--accent-blue)]" /> The Arena</h2>
        <TonConnectButton className="ton-connect-btn" />
      </div>

      <div className="glass-card bg-gradient-to-br from-[#1a1a1e] to-[#25252a] relative overflow-hidden mb-2 border border-[var(--accent-blue)]/20">
        <div className="absolute top-0 right-0 p-4 opacity-10 text-[var(--accent-blue)]">
          <Trophy size={64} />
        </div>
        <h3 className="text-xl font-bold mb-1">Top Performing</h3>
        <p className="text-hint text-sm mb-4">Subscribe to signals from verified elite traders.</p>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide hide-scrollbars">
        {['All', 'TON', 'SOL', 'BASE', 'High Winrate'].map(cat => (
          <button 
            key={cat} 
            className={`px-3 py-1.5 text-xs font-semibold rounded-full whitespace-nowrap transition-colors ${
              activeFilter === cat 
                ? 'bg-[var(--accent-blue)] text-white' 
                : 'bg-white/5 border border-white/10 text-hint hover:text-white'
            }`}
            onClick={() => setActiveFilter(cat)}
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="flex flex-col gap-3">
        {isLoading ? (
          <>
            {[1, 2, 3].map((i) => (
              <div key={i} className="glass-card flex flex-col gap-3">
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-3">
                    <Skeleton className="w-10 h-10 rounded-full" />
                    <div className="flex flex-col gap-2">
                      <Skeleton className="h-5 w-24" />
                      <Skeleton className="h-3 w-16" />
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <Skeleton className="h-6 w-16" />
                    <Skeleton className="h-3 w-12" />
                  </div>
                </div>
                <Skeleton className="w-full h-12 mt-1" />
                <Skeleton className="w-full h-10 mt-2" />
              </div>
            ))}
          </>
        ) : traders.map((trader, index) => (
          <div 
            key={trader.id} 
            className="glass-card flex flex-col gap-3 relative cursor-pointer hover:bg-white/5 transition-colors"
            onClick={() => onTraderSelect && trader.public_slug && onTraderSelect(trader.public_slug)}
          >
            <div className="flex justify-between items-start">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-black/40 flex items-center justify-center font-bold border border-white/10 shadow-inner">
                  #{index + 1}
                </div>
                <div>
                  <h3 className="text-lg font-bold flex items-center gap-1">
                    {trader.name}
                    {trader.badge === 'Verified' && <ShieldCheck size={14} className="text-[var(--accent-green)]" />}
                    {trader.badge === 'Elite' && <Star size={14} className="text-[#f1c40f]" />}
                    {trader.badge === 'Pro' && <Star size={14} className="text-[var(--accent-blue)]" />}
                  </h3>
                  <div className="text-sm text-hint">{trader.followers} Followers</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xl font-black text-profit">{trader.roi}</div>
                <div className="text-xs text-hint">Winrate: {trader.winrate}</div>
              </div>
            </div>

            {/* Mock SVG Chart */}
            <div className="w-full h-12 mt-1">
              <svg viewBox="0 0 100 30" className="w-full h-full" preserveAspectRatio="none">
                <path d={generateSparklinePath(trader.chartData || [0, 10, 5, 20, 15, 30, 25, 40, 30, 50])} fill="none" stroke="var(--accent-green)" strokeWidth="2" vectorEffect="non-scaling-stroke" />
                <path d={`${generateSparklinePath(trader.chartData || [0, 10, 5, 20, 15, 30, 25, 40, 30, 50])} L100,30 L0,30 Z`} fill="url(#grad)" opacity="0.2" />
                <defs>
                  <linearGradient id="grad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="var(--accent-green)" stopOpacity="1" />
                    <stop offset="100%" stopColor="var(--accent-green)" stopOpacity="0" />
                  </linearGradient>
                </defs>
              </svg>
            </div>

            <Dialog>
              <DialogTrigger 
                className="btn-primary mt-2 w-full" 
                onClick={(e) => e.stopPropagation()}
              >
                Subscribe • {trader.price}
              </DialogTrigger>
              <DialogContent className="w-[90vw] max-w-md rounded-2xl bg-[#1c1c1e] border-white/10 text-white p-6 shadow-2xl">
                <DialogHeader>
                  <DialogTitle className="text-xl font-bold flex items-center gap-2">
                    <Trophy size={20} className="text-[var(--accent-blue)]" />
                    Subscribe to {trader.name}
                  </DialogTitle>
                  <DialogDescription className="text-white/70 pt-2 text-sm">
                    You are about to subscribe to {trader.name}'s VIP signals for {trader.price}. This grants you 1-Click and Automated Copy-Trading access for 30 days.
                  </DialogDescription>
                </DialogHeader>
                <div className="flex flex-col gap-3 mt-2">
                  <div className="bg-black/30 p-3 rounded-xl border border-white/5 text-sm flex justify-between">
                    <span className="text-hint">Total Amount:</span>
                    <span className="font-bold">{trader.price}</span>
                  </div>
                  <button 
                    className="btn-primary w-full py-3 mt-2 text-base font-bold shadow-lg shadow-blue-500/20"
                    onClick={() => handleSubscribe(trader)}
                  >
                    Confirm & Pay
                  </button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        ))}
      </div>
    </div>
  );
};
