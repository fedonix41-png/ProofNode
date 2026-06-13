import React, { useState } from 'react';
import type { Trader, Signal } from '../types';
import { ChevronLeft, ArrowUpRight, ArrowDownRight, MessageSquare, Send, Sparkles } from 'lucide-react';

interface DetailProps {
  slug: string;
  onBack: () => void;
}

interface Message {
  sender: 'user' | 'pilot';
  text: string;
  time: string;
}

export default function TraderDetailView({ slug, onBack }: DetailProps) {
  // Mock current trader profile
  const trader: Trader = {
    id: 'trader_detailed',
    name: slug === 'crypto-wizard' ? 'Solana Whale #2' : slug === 'whale-tracker' ? 'Base Degen Alpha' : 'TON Market Maker',
    username: slug === 'crypto-wizard' ? 'sol_whale_2' : slug === 'whale-tracker' ? 'base_degen_alpha' : 'ton_market_maker',
    public_slug: slug,
    badge: slug === 'crypto-wizard' ? 'Elite' : slug === 'whale-tracker' ? 'Pro' : 'Verified',
    followers: slug === 'crypto-wizard' ? 1420 : slug === 'whale-tracker' ? 890 : 432,
    winrate: slug === 'crypto-wizard' ? '82.4%' : slug === 'whale-tracker' ? '71.2%' : '94.2%',
    roi: slug === 'crypto-wizard' ? '+142.5%' : slug === 'whale-tracker' ? '+85.2%' : '+34.2%',
    price: slug === 'crypto-wizard' ? '9.9 TON' : slug === 'whale-tracker' ? '4.5 TON' : 'FREE',
    blockchain: slug === 'crypto-wizard' ? 'SOL' : slug === 'whale-tracker' ? 'BASE' : 'TON',
    chartData: slug === 'crypto-wizard' ? [20, 35, 15, 60, 45, 90, 80, 110, 142.5] : slug === 'whale-tracker' ? [10, -5, 20, 15, 45, 30, 60, 55, 85.2] : [5, 10, 8, 15, 22, 18, 30, 28, 34.2],
    description: slug === 'crypto-wizard'
      ? 'Specializes in high-conviction microcap assets on Raydium and Jupiter. Utilizes real-time order-book sequencing to capture early pumps.'
      : slug === 'whale-tracker'
      ? 'Base chain token specialist tracking developer wallets, liquidity locks, and Uniswap pool updates.'
      : 'Intraday arbitrage bot processing high liquidity pairs on Ston.fi and DeDust.'
  };

  // Mock signals
  const signals: Signal[] = [
    {
      id: 'sig1',
      token_address: 'EQCz1_SCALE_Token_Contract...',
      blockchain: trader.blockchain,
      direction: 'BUY',
      status: 'CLOSED',
      entry_price: 1.25,
      exit_price: 1.83,
      pnl_percent: 46.4
    },
    {
      id: 'sig2',
      token_address: '0x88b_BASE_Token_Contract...',
      blockchain: trader.blockchain,
      direction: 'BUY',
      status: 'OPEN',
      entry_price: 0.082
    },
    {
      id: 'sig3',
      token_address: '5Kq3_SOL_Meme_Contract...',
      blockchain: trader.blockchain,
      direction: 'SELL',
      status: 'CLOSED',
      entry_price: 24.50,
      exit_price: 18.20,
      pnl_percent: 25.71
    }
  ];

  // AI Copilot state
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'pilot',
      text: `Hello! I am your ProofNode Co-Pilot 🫡. I'm analyzing ${trader.name}. Ask me about their current risk exposure, optimal asset allocation, or average trade frequency.`,
      time: 'Just now'
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const handleSendChat = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMsg: Message = {
      sender: 'user',
      text: chatInput,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      let reply: string;
      const inputLower = userMsg.text.toLowerCase();

      if (inputLower.includes('risk') || inputLower.includes('drawdown')) {
        reply = `${trader.name} operates with a ${slug === 'sniper-bot' ? 'low drawdown profile (< 2%) due to high frequency arbitrage.' : 'medium-to-high risk profile, commonly executing swaps on low liquidity pools with up to 15% slippage.'} Always configure a strict stop-loss in your Copy settings.`;
      } else if (inputLower.includes('allocation') || inputLower.includes('much') || inputLower.includes('budget')) {
        reply = `For ${trader.name}, we suggest starting with an allocation of no more than 10-15% of your total proxy wallet balance (e.g., 2-3 TON per trade) to properly manage exposure.`;
      } else if (inputLower.includes('frequency') || inputLower.includes('often') || inputLower.includes('time')) {
        reply = `They average about ${slug === 'sniper-bot' ? '15-20 micro-trades per hour.' : '3-5 on-chain positions per day.'} Active monitoring suggests they hold positions for an average of ${slug === 'crypto-wizard' ? '48 hours.' : '6 hours.'}`;
      } else {
        reply = `Based on current on-chain auditable telemetry, ${trader.name} shows a cumulative winrate of ${trader.winrate} across ${trader.followers} active copiers. Highly recommended to bind with 1-Click execution toggles.`;
      }

      const pilotMsg: Message = {
        sender: 'pilot',
        text: reply,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, pilotMsg]);
      setIsTyping(false);

      if ((window as any).Telegram?.WebApp?.HapticFeedback) {
        (window as any).Telegram.WebApp.HapticFeedback.impactOccurred('light');
      }
    }, 1500);
  };

  // SVG P&L line generator
  const getPLChartPath = (data: number[]) => {
    const width = 300;
    const height = 100;
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
      {/* Back button */}
      <button
        onClick={onBack}
        className="flex items-center text-hint hover:text-white transition-all text-sm w-fit gap-1 bg-white/5 px-3 py-1.5 rounded-full border border-white/10"
      >
        <ChevronLeft size={16} />
        Back to Arena
      </button>

      {/* Main card */}
      <div className="glass-card flex flex-col gap-3.5 relative overflow-hidden">
        {/* Glow glow background */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 blur-3xl -z-10 rounded-full" />
        
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-black text-white flex items-center gap-1.5">
                {trader.name}
              </h2>
              <span className="text-[10px] bg-sky-500/10 text-sky-400 px-2 py-0.5 rounded-full font-bold border border-sky-500/20">
                {trader.blockchain}
              </span>
            </div>
            <p className="text-slate-300 text-xs mt-1 leading-relaxed">{trader.description}</p>
          </div>

          <div className="text-right flex flex-col items-end">
            <span className="text-2xl font-black text-profit block leading-none">
              {trader.roi}
            </span>
            <span className="text-slate-400 text-xs">Total ROI</span>
          </div>
        </div>

        {/* Big ROI Metrics */}
        <div className="grid grid-cols-3 gap-2.5 mt-2">
          <div className="bg-black/20 p-3 rounded-xl border border-white/5 text-center">
            <span className="text-slate-400 text-[10px] block">Winrate</span>
            <span className="text-sm font-bold text-white">{trader.winrate}</span>
          </div>
          <div className="bg-black/20 p-3 rounded-xl border border-white/5 text-center">
            <span className="text-slate-400 text-[10px] block">Copiers</span>
            <span className="text-sm font-bold text-white">{trader.followers}</span>
          </div>
          <div className="bg-black/20 p-3 rounded-xl border border-white/5 text-center">
            <span className="text-slate-400 text-[10px] block">Subscription</span>
            <span className="text-sm font-bold text-white">{trader.price}</span>
          </div>
        </div>

        {/* Real Live Graph */}
        <div className="mt-3 bg-black/35 rounded-2xl p-4 border border-white/5 flex flex-col gap-2">
          <div className="flex justify-between text-xs text-slate-400 items-center">
            <span>Historical ROI curve</span>
            <span className="text-profit flex items-center font-bold">
              <ArrowUpRight size={14} /> Peak +165%
            </span>
          </div>
          <div className="w-full h-24 my-2">
            <svg viewBox="0 0 300 100" className="w-full h-full" preserveAspectRatio="none">
              <path
                d={getPLChartPath(trader.chartData)}
                fill="none"
                stroke="var(--accent-green)"
                strokeWidth="2.5"
                vectorEffect="non-scaling-stroke"
              />
              <path
                d={`${getPLChartPath(trader.chartData)} L 300 100 L 0 100 Z`}
                fill="url(#detailedGrad)"
                opacity="0.15"
              />
              <defs>
                <linearGradient id="detailedGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="var(--accent-green)" stopOpacity="1" />
                  <stop offset="100%" stopColor="var(--accent-green)" stopOpacity="0" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>
      </div>

      {/* Interactive AI Copilot chat */}
      <div className="glass-card flex flex-col gap-3">
        <div className="flex items-center justify-between mb-1 pb-2 border-b border-white/[0.06]">
          <div className="flex items-center gap-2">
            <Sparkles className="text-yellow-400 animate-pulse" size={18} />
            <h3 className="text-sm font-bold text-white">AI Trader Copilot</h3>
          </div>
          <span className="text-[10px] text-emerald-400 font-bold flex items-center gap-1">
            ● Active
          </span>
        </div>

        {/* Message logs */}
        <div className="flex flex-col gap-2.5 max-h-48 overflow-y-auto pr-1">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex flex-col max-w-[85%] rounded-2xl p-3 text-xs leading-relaxed ${
                m.sender === 'user'
                  ? 'bg-sky-500 text-white self-end rounded-tr-none shadow-md'
                  : 'bg-black/35 text-white/90 self-start rounded-tl-none border border-white/5'
              }`}
            >
              <span>{m.text}</span>
              <span className="text-[9px] text-white/40 text-right block mt-1">{m.time}</span>
            </div>
          ))}
          {isTyping && (
            <div className="bg-black/35 text-white/50 text-xs self-start rounded-2xl p-3 animate-pulse border border-white/5">
              Analyzing trade pattern...
            </div>
          )}
        </div>

        {/* Message input */}
        <form onSubmit={handleSendChat} className="flex gap-2.5 mt-2">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            className="input-glass py-2 px-3 text-xs flex-1"
            placeholder="Ask Copilot: 'Is this trader safe?'"
          />
          <button
            type="submit"
            className="btn-primary w-auto py-2.5 px-3 rounded-xl h-auto shrink-0"
          >
            <Send size={14} />
          </button>
        </form>
      </div>

      {/* Signals section */}
      <div className="glass-card flex flex-col gap-3">
        <div className="flex items-center gap-2 mb-1 justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="text-sky-400" size={20} />
            <h3 className="text-sm font-bold text-white">Audited On-chain Signals</h3>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Latest 30d logs</span>
        </div>

        <div className="flex flex-col gap-3">
          {signals.map(s => (
            <div key={s.id} className="flex justify-between items-center p-3.5 bg-black/20 rounded-2xl border border-white/5 text-xs">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <span className={`font-black uppercase px-2 py-0.5 rounded text-[10px] ${
                    s.direction === 'BUY' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                  }`}>
                    {s.direction}
                  </span>
                  <span className="text-slate-400 font-mono text-xs break-all">{s.token_address}</span>
                </div>
                <div className="text-white/80 text-[10px] mt-1 h-3 flex items-center gap-2">
                  <span>Entry: ${s.entry_price}</span>
                  {s.exit_price && <span>• Exit: ${s.exit_price}</span>}
                </div>
              </div>

              <div className="text-right">
                {s.status === 'OPEN' ? (
                  <span className="text-[10px] font-bold text-amber-500 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full">
                    ACTIVE
                  </span>
                ) : (
                  <div className={`font-bold text-sm flex items-center leading-none ${
                    s.pnl_percent && s.pnl_percent >= 0 ? 'text-profit' : 'text-loss'
                  }`}>
                    {s.pnl_percent && s.pnl_percent >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                    {s.pnl_percent}%
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
