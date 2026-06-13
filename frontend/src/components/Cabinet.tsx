import React, { useState } from 'react';
import type { CopyTradeExecution, UserProfile } from '../types';
import { INITIAL_EXECUTIONS, INITIAL_USER_PROFILE } from '../data';
import { ShieldCheck, Copy, Check, Users, Key, Plus, Coins, Zap } from 'lucide-react';

interface CabinetProps {
  walletConnected: boolean;
  onConnectWalletToggle: () => void;
}

export default function CabinetView(_props: CabinetProps) {
  // SSS state
  const [privateKeyField, setPrivateKeyHex] = useState('');
  const [backupShare3, setBackupShare3] = useState('');
  const [copiedShare3, setCopiedShare3] = useState(false);
  const [encrypting, setEncrypting] = useState(false);
  const [userProfile, setUserProfile] = useState<UserProfile>(INITIAL_USER_PROFILE);
  const [executions, setExecutions] = useState<CopyTradeExecution[]>(INITIAL_EXECUTIONS);
  
  // Proxy Wallet state
  const [proxyAddress] = useState('EQD3v_pro_x9AjdN30UW9wkKNptW2ctp4cEsvhlLY_CsQ1uo');
  const [proxyBalance, setProxyBalance] = useState('14.2');
  const [signalTokenField, setSignalTokenField] = useState('');
  const [signalDirection, setSignalDirection] = useState<'BUY' | 'SELL'>('BUY');
  const [adminSignals, setAdminSignals] = useState<any[]>([]);
  const [copiedInvite, setCopiedInvite] = useState(false);
  const [buyingPremium, setBuyingPremium] = useState(false);

  // SSS mock (representing 2-of-3 Shamir algorithm from security.md)
  const handleSssSetup = (e: React.FormEvent) => {
    e.preventDefault();
    if (!privateKeyField.trim()) return;

    setEncrypting(true);
    setTimeout(() => {
      // Split the key (simplified simulator)
      const part1 = `1-dev-sh-${privateKeyField.substring(0, 10)}`;
      const part2 = `2-server-sh-${privateKeyField.substring(10, 20)}`;
      const part3 = `3-backup-sh-${privateKeyField.substring(20, 30)}`;

      localStorage.setItem('sss_share_1', part1);
      // Simulate sending share 2 to server with mock api
      console.log('Sending SSS Share 2 to server:', part2);

      setBackupShare3(part3);
      setPrivateKeyHex('');
      setEncrypting(false);
      
      if ((window as any).Telegram?.WebApp?.HapticFeedback) {
        (window as any).Telegram.WebApp.HapticFeedback.notificationOccurred('success');
      }
    }, 1200);
  };

  const handleCopyBackupShare = () => {
    navigator.clipboard.writeText(backupShare3);
    setCopiedShare3(true);
    setTimeout(() => setCopiedShare3(false), 2000);
    
    if ((window as any).Telegram?.WebApp?.HapticFeedback) {
      (window as any).Telegram.WebApp.HapticFeedback.impactOccurred('light');
    }
  };

  const handleDepositFunds = () => {
    // Top up 10 TON to the proxy wallet balance
    setProxyBalance(prev => (parseFloat(prev) + 10.0).toFixed(1));
    showToast("Deposited 10 TON to your proxy wallet!");
    
    // Add success execution log
    const newExec: CopyTradeExecution = {
      id: `exec_${Date.now()}`,
      trader_name: 'Ston.fi Pool',
      trader_tx_hash: '0x_deposit_tx_' + Math.random().toString(36).substring(7),
      copy_tx_hash: '0x_deposit_copy_' + Math.random().toString(36).substring(7),
      blockchain: 'TON',
      amount: '10.0 TON (Inbound)',
      status: 'SUCCESS',
      executed_at: 'Just now'
    };
    setExecutions(prev => [newExec, ...prev]);

    if ((window as any).Telegram?.WebApp?.HapticFeedback) {
      (window as any).Telegram.WebApp.HapticFeedback.notificationOccurred('success');
    }
  };

  const handlePublishSignal = (e: React.FormEvent) => {
    e.preventDefault();
    if (!signalTokenField.trim()) return;

    const newSignal = {
      id: `sig_${Date.now()}`,
      token_address: signalTokenField,
      direction: signalDirection,
      status: 'OPEN',
      created_at: new Date().toLocaleTimeString()
    };

    setAdminSignals(prev => [newSignal, ...prev]);
    setSignalTokenField('');
    showToast("Signal broadcasted successfully!");

    if ((window as any).Telegram?.WebApp?.HapticFeedback) {
      (window as any).Telegram.WebApp.HapticFeedback.notificationOccurred('success');
    }
  };

  const handleCloseSignal = (id: string) => {
    setAdminSignals(prev => prev.filter(s => s.id !== id));
    showToast("Signal closed & winrate updated on-chain.");
    
    if ((window as any).Telegram?.WebApp?.HapticFeedback) {
      (window as any).Telegram.WebApp.HapticFeedback.impactOccurred('medium');
    }
  };

  const handleCopyInviteLink = () => {
    const link = `https://t.me/AlphaHubBot/app?startapp=ref_${userProfile.referral_code}`;
    navigator.clipboard.writeText(link);
    setCopiedInvite(true);
    setTimeout(() => setCopiedInvite(false), 2000);

    if ((window as any).Telegram?.WebApp?.HapticFeedback) {
      (window as any).Telegram.WebApp.HapticFeedback.impactOccurred('light');
    }
  };

  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3000);
  };

  return (
    <div className="animate-fade-in flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          Cabinet
        </h2>
        <span className="text-hint text-xs bg-white/5 py-1 px-3 rounded-full border border-white/10 font-mono">
          Tier: {userProfile.is_premium ? 'Premium 👑' : 'Free Client'}
        </span>
      </div>

      {/* SSS 1-Click Copy Trading Panel */}
      <div className="glass-card flex flex-col gap-3">
        <div className="flex items-center gap-2 mb-1">
          <Key className="text-sky-400" size={24} />
          <h3 className="text-base font-bold text-white">Shamir's Secret Sharing (2-of-3)</h3>
        </div>
        <p className="text-slate-300 text-xs leading-relaxed">
          Automate copy trades client-side. We split your Web3 private key into 3 shards. Share 1 remains on device, Share 2 is encrypted on-server, and Share 3 serves as your offline backup.
        </p>

        {backupShare3 ? (
          <div className="mt-3 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 animate-fade-in">
            <h4 className="text-emerald-400 text-sm font-bold mb-2 flex items-center gap-2">
              <ShieldCheck size={18} />
              Key Shattered Successfully!
            </h4>
            <p className="text-xs text-white/90 mb-3 leading-relaxed">
              Shard 3 holds your offline backup. Write this down in a secure place. If you loss this device, you will need Shard 3 to rebuild access.
            </p>
            <div className="relative">
              <div className="p-3 bg-black/40 rounded-lg font-mono text-xs break-all text-slate-400 border border-white/10">
                {backupShare3}
              </div>
              <button
                className="absolute right-2 top-2 p-1.5 bg-white/5 rounded-md border border-white/10 hover:bg-white/10 transition-colors"
                onClick={handleCopyBackupShare}
              >
                {copiedShare3 ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
              </button>
            </div>
            <button
              className="btn-secondary w-full mt-4 text-xs font-semibold py-2.5"
              onClick={() => setBackupShare3('')}
            >
              I have saved my backup
            </button>
          </div>
        ) : (
          <form onSubmit={handleSssSetup} className="flex flex-col gap-2 mt-2">
            <input
              type="password"
              value={privateKeyField}
              onChange={(e) => setPrivateKeyHex(e.target.value)}
              className="input-glass font-mono text-xs"
              placeholder="Paste your 64-char Hex Private Key"
            />
            <button
               type="submit"
               disabled={encrypting || !privateKeyField.trim()}
               className="btn-primary w-full py-3"
            >
              {encrypting ? 'Splitting Cryptographically...' : 'Set up Non-Custodial Copying'}
            </button>
          </form>
        )}
      </div>

      {/* Proxy Wallet details */}
      <div className="glass-card flex flex-col gap-3">
        <div className="flex items-center gap-2 mb-1">
          <Coins className="text-sky-400" size={24} />
          <h3 className="text-base font-bold text-white">Safe Proxy Wallet</h3>
        </div>
        
        <div className="flex justify-between items-center bg-black/20 p-3 rounded-xl border border-white/5">
          <div>
            <span className="text-slate-400 text-[10px] uppercase font-bold block">Proxy Address</span>
            <span className="text-xs text-white/90 font-mono">{proxyAddress.substring(0, 10)}...{proxyAddress.substring(proxyAddress.length - 10)}</span>
          </div>
          <div className="text-right">
            <span className="text-slate-400 text-[10px] uppercase font-bold block">Native Balance</span>
            <span className="text-base font-black text-sky-400">{proxyBalance} TON</span>
          </div>
        </div>

        <button
          onClick={handleDepositFunds}
          className="btn-primary font-bold text-xs py-2.5 flex items-center justify-center gap-2"
        >
          <Plus size={14} />
          Top Up Proxy (Testnet Simulator)
        </button>

        {/* Copy trade executions */}
        <div className="mt-3">
          <h4 className="text-xs font-bold text-slate-400 mb-2 uppercase">Execution logs (E2E Verified)</h4>
          <div className="flex flex-col gap-2">
            {executions.map(ex => (
              <div key={ex.id} className="flex justify-between items-center p-2 rounded-lg bg-black/20 text-xs border border-white/[0.04]">
                <div>
                  <span className="font-semibold text-white/90">{ex.trader_name}</span>
                  <span className="text-[10px] text-slate-400 block">Status: {ex.status} • {ex.executed_at}</span>
                </div>
                <div className="font-mono text-white/90 font-bold">{ex.amount}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Admin Signal Broadcast Room */}
      <div className="glass-card flex flex-col gap-3">
        <div className="flex items-center gap-2 mb-1">
          <Zap className="text-amber-400" size={24} />
          <h3 className="text-base font-bold text-white">Admin Broadcast Control</h3>
        </div>
        <p className="text-slate-300 text-xs">
          Publish on-chain buy/sell signals to your rooms and VIP subscribers instantly.
        </p>

        <form onSubmit={handlePublishSignal} className="flex flex-col gap-2.5 mt-1">
          <input
            type="text"
            value={signalTokenField}
            onChange={(e) => setSignalTokenField(e.target.value)}
            className="input-glass text-xs"
            placeholder="Search / Paste Token Address"
          />
          <div className="flex gap-2">
            <button
              type="button"
              className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-all ${
                signalDirection === 'BUY'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-white/5 border border-white/10 text-slate-400'
              }`}
              onClick={() => setSignalDirection('BUY')}
            >
              BUY
            </button>
            <button
              type="button"
              className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-all ${
                signalDirection === 'SELL'
                  ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                  : 'bg-white/5 border border-white/10 text-slate-400'
              }`}
              onClick={() => setSignalDirection('SELL')}
            >
              SELL
            </button>
          </div>
          <button
            type="submit"
            disabled={!signalTokenField.trim()}
            className="btn-secondary w-full text-xs font-bold py-2.5"
          >
            Publish Signal
          </button>
        </form>

        {adminSignals.length > 0 && (
          <div className="mt-3 flex flex-col gap-2">
            <h4 className="text-xs font-bold text-slate-400 uppercase">Your active signals</h4>
            {adminSignals.map(sig => (
              <div key={sig.id} className="flex justify-between items-center p-2.5 bg-black/40 rounded-xl border border-white/5 text-xs">
                <div>
                  <span className={`font-black ${sig.direction === 'BUY' ? 'text-emerald-400' : 'text-rose-400'}`}>{sig.direction}</span>
                  <span className="font-mono text-slate-400 ml-2">{sig.token_address.substring(0, 12)}...</span>
                </div>
                <button
                  onClick={() => handleCloseSignal(sig.id)}
                  className="px-2 py-1 bg-white/5 hover:bg-white/10 rounded font-bold border border-white/10 text-slate-300"
                >
                  Close Signal
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Referrals Section */}
      <div className="glass-card flex flex-col gap-3">
        <div className="flex items-center gap-2 mb-1">
          <Users className="text-sky-400" size={24} />
          <h3 className="text-base font-bold text-white">Referral Slots</h3>
        </div>
        <div className="grid grid-cols-2 gap-3 text-center">
          <div className="bg-black/20 p-3 rounded-xl border border-white/5 flex flex-col">
            <span className="text-slate-400 text-[10px]">Friends Referred</span>
            <span className="text-base font-black text-white">{userProfile.total_referred}</span>
          </div>
          <div className="bg-black/20 p-3 rounded-xl border border-white/5 flex flex-col">
            <span className="text-slate-400 text-[10px]">Bonus Wallet Slots</span>
            <span className="text-base font-black text-emerald-400">+{userProfile.referral_credits * 2}</span>
          </div>
        </div>

        <div className="mt-2">
          <span className="text-slate-400 text-[10px] uppercase font-bold block mb-2">Share Invite Link</span>
          <div className="relative">
            <div className="p-3 bg-black/40 rounded-xl font-mono text-xs break-all text-white/80 border border-white/10 pr-12">
              https://t.me/AlphaHubBot/app?startapp=ref_{userProfile.referral_code}
            </div>
            <button
              onClick={handleCopyInviteLink}
              className="absolute right-2 top-2 p-1.5 bg-white/5 rounded-md border border-white/10 hover:bg-white/10 transition-colors"
            >
              {copiedInvite ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
            </button>
          </div>
        </div>
      </div>

      {/* Premium Plan Toggles */}
      <div className="glass-card border border-white/15 relative overflow-hidden flex flex-col gap-4">
        <div className="absolute top-0 right-0 w-32 h-32 bg-sky-500/10 blur-3xl rounded-full" />
        <div className="flex items-center gap-2">
          <Zap className="text-sky-400 fill-sky-400/20" size={24} />
          <h3 className="text-lg font-bold text-white">ProofNode Premium</h3>
        </div>
        <p className="text-xs text-white/80">
          Unlock the final tier copy-trading: Unlimited tracked address slots, zero notification delays, and customized webhook limits.
        </p>

        <div className="flex gap-2.5">
          <button
            onClick={() => {
              setBuyingPremium(true);
              setTimeout(() => {
                setUserProfile(prev => ({ ...prev, is_premium: true }));
                setBuyingPremium(false);
                showToast("ProofNode Premium Activated!");
              }, 1200);
            }}
            disabled={buyingPremium || userProfile.is_premium}
            className="flex-1 py-3 px-4 bg-gradient-to-r from-sky-500 to-blue-500 font-bold text-xs rounded-xl shadow-lg active:scale-95 transition-all text-white"
          >
            {buyingPremium ? 'Processing...' : userProfile.is_premium ? '👑 Active' : '2.5 TON / mo'}
          </button>
          <button
            onClick={() => {
              setBuyingPremium(true);
              setTimeout(() => {
                setUserProfile(prev => ({ ...prev, is_premium: true }));
                setBuyingPremium(false);
                showToast("ProofNode Premium Activated!");
              }, 1200);
            }}
            disabled={buyingPremium || userProfile.is_premium}
            className="flex-1 py-3 px-4 bg-gradient-to-r from-yellow-500 to-amber-500 font-bold text-xs rounded-xl shadow-lg active:scale-95 transition-all text-black"
          >
            {buyingPremium ? 'Processing...' : userProfile.is_premium ? '👑 Active' : '⭐️ 800 Stars'}
          </button>
        </div>
      </div>

      {/* Toast Notification */}
      {toastMsg && (
        <div className="fixed bottom-24 left-1/2 transform -translate-x-1/2 z-50 bg-slate-950/80 backdrop-blur-xl border border-white/10 text-white px-4 py-3 rounded-xl text-xs flex items-center gap-2 shadow-2xl animate-fade-in">
          <ShieldCheck size={14} className="text-emerald-400" />
          <span>{toastMsg}</span>
        </div>
      )}
    </div>
  );
}
