import { create } from 'zustand';
import { fetchApi } from '../lib/api';

export interface WalletStats {
  total_balance_usd: number;
  active_trades: number;
  daily_pnl: number;
  win_rate: number;
  recent_activity: any[];
}

interface WalletState {
  stats: WalletStats | null;
  isLoading: boolean;
  error: string | null;
  fetchStats: () => Promise<void>;
}

export const useWalletStore = create<WalletState>((set) => ({
  stats: null,
  isLoading: false,
  error: null,
  fetchStats: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await fetchApi('/api/wallets/tracker/stats');
      set({ stats: data, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },
}));
