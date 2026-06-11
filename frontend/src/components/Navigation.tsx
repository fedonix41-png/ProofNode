import React from 'react';
import { Radar, TrendingUp, User } from 'lucide-react';

export type Tab = 'radar' | 'leaderboard' | 'cabinet';

interface NavigationProps {
  activeTab: Tab;
  setActiveTab: (tab: Tab) => void;
}

export const Navigation: React.FC<NavigationProps> = ({ activeTab, setActiveTab }) => {
  return (
    <nav className="bottom-nav">
      <a 
        className={`nav-item ${activeTab === 'radar' ? 'active' : ''}`} 
        onClick={(e) => { e.preventDefault(); setActiveTab('radar'); }}
        href="#radar"
      >
        <Radar size={24} />
        <span>Radar</span>
      </a>
      
      <a 
        className={`nav-item ${activeTab === 'leaderboard' ? 'active' : ''}`} 
        onClick={(e) => { e.preventDefault(); setActiveTab('leaderboard'); }}
        href="#leaderboard"
      >
        <TrendingUp size={24} />
        <span>Arena</span>
      </a>
      
      <a 
        className={`nav-item ${activeTab === 'cabinet' ? 'active' : ''}`} 
        onClick={(e) => { e.preventDefault(); setActiveTab('cabinet'); }}
        href="#cabinet"
      >
        <User size={24} />
        <span>Cabinet</span>
      </a>
    </nav>
  );
};
