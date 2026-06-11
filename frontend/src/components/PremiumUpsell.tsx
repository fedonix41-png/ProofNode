import React, { useState } from 'react';
import { Star, Zap, Infinity, ShieldCheck } from 'lucide-react';
import { fetchApi } from '../lib/api';
import { toast } from './ui/Toaster';

export const PremiumUpsell: React.FC = () => {
  const [isProcessing, setIsProcessing] = useState(false);

  const handlePurchase = async (method: 'TON' | 'STARS') => {
    setIsProcessing(true);
    try {
      // Mock payment flow
      console.log(`Initiating ${method} payment...`);
      
      const txHash = `mock_tx_${Date.now()}`;
      
      await fetchApi('/api/subscriptions/premium', {
        method: 'POST',
        body: JSON.stringify({
          tx_hash: txHash,
          payment_method: method
        })
      });
      
      toast('Premium purchased successfully!', 'success');
      // Ideally we should reload user state here or notify parent component
      
    } catch (e: any) {
      toast(`Error purchasing premium: ${e.message}`, 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="glass-card flex flex-col gap-4 border border-[var(--accent-blue)]/50 relative overflow-hidden">
      <div className="absolute top-0 right-0 w-32 h-32 bg-[var(--accent-blue)]/20 blur-3xl -z-10 rounded-full" />
      
      <div className="flex items-center gap-2">
        <Star className="text-[var(--accent-blue)] fill-[var(--accent-blue)]" size={24} />
        <h3 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
          ProofNode Premium
        </h3>
      </div>
      
      <p className="text-sm text-white/80">
        Unlock the full potential of your copy-trading experience with exclusive tools and unlimited access.
      </p>
      
      <ul className="flex flex-col gap-2 my-2 text-sm">
        <li className="flex items-center gap-2">
          <Infinity size={16} className="text-[var(--accent-green)]" />
          <span>Unlimited Monitored Wallets</span>
        </li>
        <li className="flex items-center gap-2">
          <Zap size={16} className="text-[var(--accent-green)]" />
          <span>Instant Notifications (No 10m delay)</span>
        </li>
        <li className="flex items-center gap-2">
          <ShieldCheck size={16} className="text-[var(--accent-green)]" />
          <span>Exclusive "Top 100 Traders" List</span>
        </li>
      </ul>
      
      <div className="flex gap-2 mt-2">
        <button 
          className="flex-1 py-3 px-4 bg-gradient-to-r from-blue-600 to-blue-500 rounded-xl font-bold text-sm shadow-lg shadow-blue-500/20 active:scale-95 transition-all"
          onClick={() => handlePurchase('TON')}
          disabled={isProcessing}
        >
          {isProcessing ? 'Processing...' : '2.5 TON / mo'}
        </button>
        <button 
          className="flex-1 py-3 px-4 bg-gradient-to-r from-yellow-600 to-yellow-500 rounded-xl font-bold text-sm shadow-lg shadow-yellow-500/20 active:scale-95 transition-all text-black"
          onClick={() => handlePurchase('STARS')}
          disabled={isProcessing}
        >
          {isProcessing ? 'Processing...' : '⭐️ 800 Stars'}
        </button>
      </div>
      <p className="text-center text-xs text-hint mt-1">~$15 USD equivalent</p>
    </div>
  );
};
