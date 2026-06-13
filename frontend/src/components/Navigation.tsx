import React from 'react';
import { Radar, Trophy, User } from 'lucide-react';

export type Tab = 'radar' | 'leaderboard' | 'cabinet';

interface NavigationProps {
  activeTab: Tab;
  setActiveTab: (tab: Tab) => void;
  selectedTraderSlug?: string | null;
  t: any;
}

export const Navigation: React.FC<NavigationProps> = ({ activeTab, setActiveTab, selectedTraderSlug, t }) => {
  return (
    <nav className="bottom-nav max-w-md mx-auto">
      <button
        onClick={() => setActiveTab('radar')}
        className={`nav-item ${activeTab === 'radar' && !selectedTraderSlug ? 'active' : ''}`}
      >
        <Radar size={20} />
        <span>{t.radar_tab}</span>
      </button>

      <button
        onClick={() => setActiveTab('leaderboard')}
        className={`nav-item ${activeTab === 'leaderboard' && !selectedTraderSlug ? 'active' : ''}`}
      >
        <Trophy size={20} />
        <span>{t.arena_tab}</span>
      </button>

      <button
        onClick={() => setActiveTab('cabinet')}
        className={`nav-item ${activeTab === 'cabinet' && !selectedTraderSlug ? 'active' : ''}`}
      >
        <User size={20} />
        <span>{t.cabinet_tab}</span>
      </button>
    </nav>
  );
};
