import React, { useEffect, useState } from 'react';
import { Users, Copy, CheckCircle2 } from 'lucide-react';
import { fetchApi } from '../lib/api';
import { Skeleton } from './ui/Skeleton';

interface ReferralStats {
  user_id: number;
  referral_code: string;
  total_referred: number;
  referral_credits: number;
}

export const Referrals: React.FC = () => {
  const [stats, setStats] = useState<ReferralStats | null>(null);
  const [isCopied, setIsCopied] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchReferrals = async () => {
      try {
        const data = await fetchApi('/api/users/referrals');
        if (data) {
          setStats(data);
        }
      } catch (e) {
        console.error('Failed to fetch referrals:', e);
      } finally {
        setIsLoading(false);
      }
    };
    fetchReferrals();
  }, []);

  const getReferralLink = () => {
    if (!stats) return '';
    const botUsername = 'AlphaHubBot'; // Or whatever is configured
    return `https://t.me/${botUsername}/app?startapp=ref_${stats.referral_code}`;
  };

  const handleCopy = () => {
    const link = getReferralLink();
    if (!link) return;
    
    navigator.clipboard.writeText(link);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
    
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.notificationOccurred('success');
    }
  };

  return (
    <div className="glass-card flex flex-col gap-3">
      <div className="flex items-center gap-2 mb-2">
        <Users className="text-[var(--accent-blue)]" size={24} />
        <h3 className="text-lg font-bold">Referral Program</h3>
      </div>
      
      {isLoading ? (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-2">
            <Skeleton className="h-16 rounded-lg" />
            <Skeleton className="h-16 rounded-lg" />
          </div>
          <div className="mt-2">
            <Skeleton className="h-4 w-24 mb-2" />
            <Skeleton className="h-10 rounded-lg" />
          </div>
        </div>
      ) : stats ? (
        <>
          <div className="grid grid-cols-2 gap-2">
            <div className="flex flex-col bg-black/20 p-3 rounded-lg border border-white/5">
              <span className="text-sm text-hint">Friends Invited</span>
              <span className="text-xl font-bold">{stats.total_referred}</span>
            </div>
            <div className="flex flex-col bg-black/20 p-3 rounded-lg border border-white/5">
              <span className="text-sm text-hint">Bonus Wallet Slots</span>
              <span className="text-xl font-bold text-[var(--accent-green)]">+{stats.referral_credits * 2}</span>
            </div>
          </div>
          
          <div className="mt-2">
            <p className="text-xs text-hint mb-2">Your Invite Link</p>
            <div className="relative">
              <div className="p-3 bg-black/40 rounded-lg font-mono text-xs break-all text-white/80 border border-white/10 pr-10">
                {getReferralLink()}
              </div>
              <button 
                className="absolute right-2 top-2 p-1.5 bg-[var(--secondary-bg)] rounded-md border border-white/10 hover:bg-white/10 transition-colors"
                onClick={handleCopy}
              >
                {isCopied ? <CheckCircle2 size={16} className="text-[var(--accent-green)]" /> : <Copy size={16} />}
              </button>
            </div>
          </div>
        </>
      ) : (
        <div className="text-sm text-red-400">Failed to load referral data.</div>
      )}
    </div>
  );
};
