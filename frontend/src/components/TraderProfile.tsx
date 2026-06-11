import React, { useEffect, useState } from 'react';
import { ArrowLeft, TrendingUp, CheckCircle2 } from 'lucide-react';
import { fetchApi } from '../lib/api';
import { toast } from './ui/Toaster';

interface TraderProfileProps {
  slug: string;
  onBack: () => void;
}

export const TraderProfile: React.FC<TraderProfileProps> = ({ slug, onBack }) => {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await fetchApi(`/api/traders/${slug}`);
        setProfile(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [slug]);

  if (loading) {
    return <div className="p-4 text-center">Loading profile...</div>;
  }

  if (error || !profile) {
    return (
      <div className="p-4">
        <button className="mb-4 flex items-center text-hint hover:text-white" onClick={onBack}>
          <ArrowLeft size={20} className="mr-2" /> Back
        </button>
        <div className="text-red-400">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in flex flex-col gap-4">
      <button className="flex items-center text-hint hover:text-white" onClick={onBack}>
        <ArrowLeft size={20} className="mr-2" /> Back
      </button>

      <div className="glass-card flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold flex items-center gap-2">
              {profile.title}
              {profile.is_verified && <CheckCircle2 size={18} className="text-[var(--accent-blue)]" />}
            </h2>
            <p className="text-hint text-sm mt-1">{profile.description || "No description provided."}</p>
          </div>
        </div>

        <div className="flex gap-4 mt-2">
          <div className="flex-1 bg-black/20 rounded-xl p-3 border border-white/5 text-center">
            <div className="text-hint text-xs mb-1">Winrate</div>
            <div className="font-bold text-[var(--accent-green)]">{profile.stats?.winrate || '0'}%</div>
          </div>
          <div className="flex-1 bg-black/20 rounded-xl p-3 border border-white/5 text-center">
            <div className="text-hint text-xs mb-1">ROI</div>
            <div className="font-bold text-white">+{profile.stats?.cumulative_roi || '0'}%</div>
          </div>
        </div>

        <button 
          className="btn-primary w-full mt-2" 
          onClick={() => {
            if (window.Telegram?.WebApp?.HapticFeedback) {
              window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
            }
            toast('Setup 1-Click Copy in Cabinet!', 'info');
          }}
        >
          <TrendingUp size={18} className="mr-2 inline" /> Copy Trade
        </button>
      </div>

      <div className="glass-card flex flex-col gap-3">
        <h3 className="text-lg font-bold">Recent Signals</h3>
        {!profile.recent_signals || profile.recent_signals.length === 0 ? (
          <p className="text-hint text-sm">No signals found.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {profile.recent_signals.map((signal: any) => (
              <div key={signal.id} className="flex justify-between items-center p-3 bg-black/30 rounded-xl border border-white/5">
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`font-bold text-sm ${signal.direction === 'BUY' ? 'text-[var(--accent-green)]' : 'text-[var(--accent-red)]'}`}>
                      {signal.direction}
                    </span>
                    <span className="font-mono text-xs">{signal.token_address.substring(0,8)}...</span>
                  </div>
                  <div className="text-xs text-hint mt-1">Status: {signal.status}</div>
                </div>
                <div className="text-right">
                  {signal.pnl_percent !== null && signal.pnl_percent !== undefined && (
                    <div className={`font-bold text-sm ${parseFloat(signal.pnl_percent) >= 0 ? 'text-[var(--accent-green)]' : 'text-[var(--accent-red)]'}`}>
                      {parseFloat(signal.pnl_percent) >= 0 ? '+' : ''}{parseFloat(signal.pnl_percent).toFixed(2)}%
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
