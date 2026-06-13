import type { Trader, MonitoredWallet, CopyTradeExecution, UserProfile } from './types';

export const INITIAL_TRADERS: Trader[] = [
  {
    id: 'trader1',
    name: 'Solana Whale #2',
    username: 'sol_whale_2',
    public_slug: 'crypto-wizard',
    badge: 'Elite',
    followers: 1420,
    winrate: '82.4%',
    roi: '+142.5%',
    price: '9.9 TON',
    blockchain: 'SOL',
    chartData: [20, 35, 15, 60, 45, 90, 80, 110, 142.5],
    description: 'Specializes in identifying hyper-growth meme tokens on Solana before they trending. Average holding time: 48 hours. Aggressive risk profile.',
    is_verified: true
  },
  {
    id: 'trader2',
    name: 'Base Degen Alpha',
    username: 'base_degen_alpha',
    public_slug: 'whale-tracker',
    badge: 'Pro',
    followers: 890,
    winrate: '71.2%',
    roi: '+85.2%',
    price: '4.5 TON',
    blockchain: 'BASE',
    chartData: [10, -5, 20, 15, 45, 30, 60, 55, 85.2],
    description: 'High-frequency degen trader on Base chain. Leverages liquidity pool additions and contracts deployments. Mid-term holding. Strictly risk managed.',
    is_verified: true
  },
  {
    id: 'trader3',
    name: 'TON Market Maker',
    username: 'ton_market_maker',
    public_slug: 'sniper-bot',
    badge: 'Verified',
    followers: 432,
    winrate: '94.2%',
    roi: '+34.2%',
    price: 'FREE',
    blockchain: 'TON',
    chartData: [5, 10, 8, 15, 22, 18, 30, 28, 34.2],
    description: 'Sniper-grade algorithmic bot placing micro-bids on Ston.fi and DeDust. Almost zero drawdown profile. Intended for consistent conservative compounding.'
  }
];

export const INITIAL_MONITORED: MonitoredWallet[] = [
  {
    id: 'mw1',
    address: '0x71c...a4',
    blockchain: 'SOL',
    label: 'Raydium Sniper Wallet',
    pnl: '+142.5%',
    isPositive: true,
    push: true,
    public_slug: 'crypto-wizard'
  },
  {
    id: 'mw2',
    address: '0x88b...1f',
    blockchain: 'BASE',
    label: 'Uniswap Whitelist Shark',
    pnl: '-12.4%',
    isPositive: false,
    push: false,
    public_slug: 'whale-tracker'
  },
  {
    id: 'mw3',
    address: 'EQ_19...z8',
    blockchain: 'TON',
    label: 'Ston.fi Alpha Liquidity',
    pnl: '+34.2%',
    isPositive: true,
    push: true,
    public_slug: 'sniper-bot'
  }
];

export const INITIAL_USER_PROFILE: UserProfile = {
  id: 123456789,
  username: "alpha_user",
  is_premium: false,
  referral_code: "b3f0wYh",
  referral_credits: 2,
  total_referred: 3
};

export const INITIAL_EXECUTIONS: CopyTradeExecution[] = [
  {
    id: 'exec1',
    trader_name: 'Solana Whale #2',
    trader_tx_hash: '5Kq3...9hj2',
    copy_tx_hash: '3pQr...tx88',
    blockchain: 'SOL',
    amount: '10.5 SOL',
    status: 'SUCCESS',
    executed_at: '2026-06-11 12:40'
  },
  {
    id: 'exec2',
    trader_name: 'Base Degen Alpha',
    trader_tx_hash: '0xdef456...a10',
    copy_tx_hash: '0x99a...662b',
    blockchain: 'BASE',
    amount: '0.2 WETH',
    status: 'SUCCESS',
    executed_at: '2026-06-11 09:12'
  },
  {
    id: 'exec3',
    trader_name: 'TON Market Maker',
    trader_tx_hash: '0xabc123...4d2',
    copy_tx_hash: 'mock_tx_failed_993',
    blockchain: 'TON',
    amount: '50 TON',
    status: 'FAILED',
    executed_at: '2026-06-10 18:31'
  }
];
