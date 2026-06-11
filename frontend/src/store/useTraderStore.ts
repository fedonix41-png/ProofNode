import { create } from 'zustand';
import { fetchApi } from '../lib/api';

export interface Trader {
  id: string;
  admin_id: number;
  telegram_username: string;
  wallet_address: string;
  blockchain: string;
  win_rate: number;
  winrate?: string;
  total_pnl: number;
  subscribers_count: number;
  performance_score: number;
  public_slug?: string;
  name?: string;
  title?: string;
  badge?: string;
  followers?: string | number;
  roi?: string;
  price?: string;
  chartData?: number[];
}

interface TraderState {
  traders: Trader[];
  isLoading: boolean;
  error: string | null;
  fetchTraders: (filters?: { blockchain?: string; high_winrate?: boolean }) => Promise<void>;
}

export const useTraderStore = create<TraderState>((set) => ({
  traders: [],
  isLoading: false,
  error: null,
  fetchTraders: async (filters?: { blockchain?: string; high_winrate?: boolean }) => {
    set({ isLoading: true, error: null });
    try {
      let url = '/api/traders';
      const params = new URLSearchParams();
      if (filters?.blockchain && ['TON', 'SOL', 'BASE'].includes(filters.blockchain)) {
        params.append('blockchain', filters.blockchain);
      }
      if (filters?.high_winrate) {
        params.append('high_winrate', 'true');
      }
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      const data = await fetchApi(url);
      set({ traders: data, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },
}));
