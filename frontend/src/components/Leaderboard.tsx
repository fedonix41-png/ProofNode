import React, { useState } from 'react';
import { TonConnectButton, useTonConnectUI, useTonWallet } from '@tonconnect/ui-react';
import { Trophy, Star, ShieldCheck } from 'lucide-react';

const TRADERS = [
  { id: 1, name: 'Crypto Wizard', badge: 'Pro', roi: '+842%', winrate: '78%', followers: 1204, price: '10 TON', public_slug: 'crypto-wizard' },
  { id: 2, name: 'Whale Tracker', badge: 'Elite', roi: '+450%', winrate: '65%', followers: 890, price: '5 TON', public_slug: 'whale-tracker' },
  { id: 3, name: 'Sniper Bot', badge: 'Verified', roi: '+310%', winrate: '82%', followers: 432, price: 'FREE', public_slug: 'sniper-bot' }
];

interface LeaderboardProps {
  onTraderSelect?: (slug: string) => void;
}

export const Leaderboard: React.FC<LeaderboardProps> = ({ onTraderSelect }) => {
  const [tonConnectUI] = useTonConnectUI();
  const wallet = useTonWallet();

  const handleSubscribe = async (trader: any) => {
    if (!wallet) {
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred('warning');
      }
      alert('Please connect your TON wallet first');
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
      alert(`Subscribed to ${trader.name}!`);

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

      <div className="flex flex-col gap-3">
        {TRADERS.map((trader, index) => (
          <div 
            key={trader.id} 
            className="glass-card flex flex-col gap-3 relative cursor-pointer hover:bg-white/5 transition-colors"
            onClick={() => onTraderSelect && onTraderSelect(trader.public_slug)}
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
                <path d={`M0,30 L10,25 L20,28 L30,20 L40,22 L50,15 L60,18 L70,10 L80,5 L90,8 L100,2`} fill="none" stroke="var(--accent-green)" strokeWidth="2" vectorEffect="non-scaling-stroke" />
                <path d={`M0,30 L10,25 L20,28 L30,20 L40,22 L50,15 L60,18 L70,10 L80,5 L90,8 L100,2 L100,30 Z`} fill="url(#grad)" opacity="0.2" />
                <defs>
                  <linearGradient id="grad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="var(--accent-green)" stopOpacity="1" />
                    <stop offset="100%" stopColor="var(--accent-green)" stopOpacity="0" />
                  </linearGradient>
                </defs>
              </svg>
            </div>

            <button 
              className="btn-primary mt-2" 
              onClick={() => handleSubscribe(trader)}
            >
              Subscribe • {trader.price}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
