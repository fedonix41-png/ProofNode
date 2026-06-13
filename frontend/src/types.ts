export interface Trader {
  id: string | number;
  name: string;
  username: string;
  public_slug: string;
  badge: 'Verified' | 'Elite' | 'Pro' | string;
  followers: number;
  winrate: string;
  roi: string;
  price: string;
  blockchain: 'TON' | 'SOL' | 'BASE';
  chartData: number[];
  description?: string;
  is_verified?: boolean;
}

export interface Signal {
  id: string;
  token_address: string;
  blockchain: 'TON' | 'SOL' | 'BASE';
  direction: 'BUY' | 'SELL';
  entry_price?: number;
  exit_price?: number;
  pnl_percent?: number;
  status: 'OPEN' | 'CLOSED';
}

export interface MonitoredWallet {
  id: string;
  address: string;
  blockchain: 'TON' | 'SOL' | 'BASE';
  label: string;
  pnl: string;
  isPositive: boolean;
  push: boolean;
  public_slug?: string;
}

export interface CopyTradeExecution {
  id: string;
  trader_name: string;
  trader_tx_hash: string;
  copy_tx_hash: string;
  blockchain: 'TON' | 'SOL' | 'BASE';
  amount: string;
  status: 'SUCCESS' | 'FAILED';
  executed_at: string;
}

export interface UserProfile {
  id: number;
  username: string;
  is_premium: boolean;
  premium_expires_at?: string;
  referral_code: string;
  referral_credits: number;
  total_referred: number;
}
