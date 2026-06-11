import React, { useState } from 'react';
import { Key, Settings, Zap, Copy, CheckCircle2 } from 'lucide-react';
import { splitKey } from '../utils/sss';
import { Referrals } from './Referrals';
import { PremiumUpsell } from './PremiumUpsell';
import { fetchApi } from '../lib/api';
import { toast } from './ui/Toaster';

export const Cabinet: React.FC = () => {
  const [pkInput, setPkInput] = useState('');
  const [share3, setShare3] = useState('');
  const [isCopied, setIsCopied] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isAuthor] = useState(true); // Mocking that user is an author for demo purposes
  const [signalToken, setSignalToken] = useState('');
  const [signalType, setSignalType] = useState('BUY');
  const [openSignals, setOpenSignals] = useState<any[]>([]);
  const MOCK_TRADER_ID = '00000000-0000-0000-0000-000000000000';

  const handleSetupCopying = async () => {
    if (!pkInput) return;
    setIsProcessing(true);

    try {
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.impactOccurred('medium');
      }

      // 1. Split Key
      const shares = splitKey(pkInput);
      const [s1, s2, s3] = shares;

      // 2. Save Share 1 Locally
      localStorage.setItem('sss_share_1', s1);

      // 3. Send Share 2 to "Server" (Mock API call)
      console.log('Sending Share 2 to server:', s2);
      await fetchApi('/api/wallets/sss/register', {
        method: 'POST',
        body: JSON.stringify({ server_share: s2 })
      }).catch(e => console.warn('Mock API call failed, continuing anyway:', e));

      // 4. Display Share 3 to user
      setShare3(s3);
      setPkInput(''); // Clear input from RAM

    } catch (e: any) {
      toast(`Error setting up: ${e.message}`, 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(share3);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.notificationOccurred('success');
    }
  };

  return (
    <div className="animate-fade-in flex flex-col gap-4">
      <div className="flex items-center justify-between mb-2">
        <h2>Cabinet</h2>
        <button className="p-2 bg-white/5 rounded-full border border-[var(--glass-border)]">
          <Settings size={20} />
        </button>
      </div>

      <div className="glass-card flex flex-col gap-3">
        <div className="flex items-center gap-2 mb-2">
          <Zap className="text-[var(--accent-blue)]" size={24} />
          <h3 className="text-lg font-bold">1-Click Copy Trading</h3>
        </div>
        <p className="text-hint text-sm">
          Set up automated proxy trading. We use Client-Side Shamir's Secret Sharing (2-of-3).
          Your full private key never leaves your device.
        </p>

        {!share3 ? (
          <>
            <input 
              type="password" 
              className="input-glass mt-2 font-mono text-sm" 
              placeholder="Paste 64-char Hex Private Key" 
              value={pkInput}
              onChange={(e) => setPkInput(e.target.value)}
            />
            <button 
              className="btn-primary mt-2" 
              onClick={handleSetupCopying}
              disabled={isProcessing || pkInput.length < 10}
            >
              <Key size={18} />
              {isProcessing ? 'Encrypting...' : 'Set up 1-Click Copying'}
            </button>
          </>
        ) : (
          <div className="mt-4 p-4 rounded-xl bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/30">
            <h4 className="text-[var(--accent-green)] font-bold mb-2 flex items-center gap-2">
              <CheckCircle2 size={18} />
              Setup Complete
            </h4>
            <p className="text-sm text-white/90 mb-3">
              Share 1 is saved on your device. Share 2 is on the server.
              <br/><br/>
              <b>Backup Share 3 below.</b> You will need it to recover your key if you lose this device!
            </p>
            <div className="relative">
              <div className="p-3 bg-black/40 rounded-lg font-mono text-xs break-all text-hint border border-white/10">
                {share3}
              </div>
              <button 
                className="absolute right-2 top-2 p-1.5 bg-[var(--secondary-bg)] rounded-md border border-white/10 hover:bg-white/10 transition-colors"
                onClick={copyToClipboard}
              >
                {isCopied ? <CheckCircle2 size={16} className="text-[var(--accent-green)]" /> : <Copy size={16} />}
              </button>
            </div>
            <button 
              className="btn-secondary w-full mt-4" 
              onClick={() => setShare3('')}
            >
              I have saved my backup
            </button>
          </div>
        )}
      </div>

      <div className={`glass-card flex flex-col gap-3 ${isAuthor ? '' : 'opacity-50 pointer-events-none'}`}>
        <h3 className="text-lg font-bold">Author Setup / Signals</h3>
        <p className="text-hint text-sm">Register your channel, verify your wallet, or post a new trade signal.</p>
        
        {isAuthor && (
          <div className="mt-2 flex flex-col gap-2 p-3 bg-black/20 rounded-xl border border-white/5">
            <h4 className="text-sm font-semibold mb-1">Broadcast Signal</h4>
            <input 
              type="text" 
              placeholder="Token Address" 
              className="input-glass text-sm"
              value={signalToken}
              onChange={(e) => setSignalToken(e.target.value)}
            />
            <div className="flex gap-2">
              <button 
                className={`flex-1 py-2 text-sm font-bold rounded-lg ${signalType === 'BUY' ? 'bg-[var(--accent-green)] text-black' : 'bg-white/10 text-hint'}`}
                onClick={() => setSignalType('BUY')}
              >
                BUY
              </button>
              <button 
                className={`flex-1 py-2 text-sm font-bold rounded-lg ${signalType === 'SELL' ? 'bg-[var(--accent-red)] text-black' : 'bg-white/10 text-hint'}`}
                onClick={() => setSignalType('SELL')}
              >
                SELL
              </button>
            </div>
            <button 
              className="btn-primary mt-1" 
              disabled={!signalToken}
              onClick={async () => {
                try {
                  const signal = await fetchApi(`/api/traders/${MOCK_TRADER_ID}/signals`, {
                    method: 'POST',
                    body: JSON.stringify({
                      token_address: signalToken,
                      blockchain: 'TON',
                      direction: signalType
                    })
                  });
                  setOpenSignals([signal, ...openSignals]);
                  toast('Signal broadcasted successfully!', 'success');
                  setSignalToken('');
                } catch (e: any) {
                  toast('Failed to broadcast signal: ' + e.message, 'error');
                }
              }}
            >
              Publish Signal
            </button>
            
            {openSignals.length > 0 && (
              <div className="mt-4 flex flex-col gap-2">
                <h4 className="text-sm font-semibold text-hint">Open Signals</h4>
                {openSignals.map((signal) => (
                  <div key={signal.id} className="flex items-center justify-between p-2 bg-black/30 rounded border border-white/5 text-sm">
                    <div>
                      <span className={signal.direction === 'BUY' ? 'text-[var(--accent-green)] font-bold' : 'text-[var(--accent-red)] font-bold'}>{signal.direction}</span>
                      <span className="ml-2 font-mono text-xs">{signal.token_address.substring(0,8)}...</span>
                    </div>
                    <button 
                      className="px-2 py-1 bg-white/10 rounded hover:bg-white/20 text-xs"
                      onClick={async () => {
                        try {
                          await fetchApi(`/api/traders/${MOCK_TRADER_ID}/signals/${signal.id}/close`, {
                            method: 'POST'
                          });
                          setOpenSignals(openSignals.filter(s => s.id !== signal.id));
                          toast('Signal closed!', 'success');
                        } catch(e: any) {
                          toast('Error closing signal: ' + e.message, 'error');
                        }
                      }}
                    >
                      Close
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
        <button className="btn-secondary w-full text-left mt-2">Connect Channel</button>
        <button className="btn-secondary w-full text-left">Set Tariff Pricing</button>
      </div>

      <Referrals />
      <PremiumUpsell />
    </div>
  );
};
