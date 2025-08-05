import React, { createContext, ReactNode, useContext, useEffect } from 'react';
import { useGamificationStore } from '../stores/gamificationStore';

interface GamificationContextType {
  currentLevel: number;
  currentXP: number;
  addXP: (amount: number, reason?: string) => void;
  unlockAchievement: (achievementId: string) => void;
}

const GamificationContext = createContext<GamificationContextType | undefined>(undefined);

interface GamificationProviderProps {
  children: ReactNode;
}

export const GamificationProvider: React.FC<GamificationProviderProps> = ({ children }) => {
  const { 
    currentLevel, 
    currentXP, 
    addXP, 
    unlockAchievement,
    updateStats,
    checkAchievements
  } = useGamificationStore();

  useEffect(() => {
    // Initialize session tracking
    const sessionStart = Date.now();
    
    // Update last active time
    updateStats({ lastActive: new Date() });
    
    // Check for time-based achievements
    checkAchievements();

    // Track session time
    const interval = setInterval(() => {
      const sessionTime = Math.floor((Date.now() - sessionStart) / 1000);
      updateStats({ sessionTime });
    }, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [updateStats, checkAchievements]);

  const contextValue: GamificationContextType = {
    currentLevel,
    currentXP,
    addXP,
    unlockAchievement
  };

  return (
    <GamificationContext.Provider value={contextValue}>
      {children}
    </GamificationContext.Provider>
  );
};

export const useGamification = () => {
  const context = useContext(GamificationContext);
  if (context === undefined) {
    throw new Error('useGamification must be used within a GamificationProvider');
  }
  return context;
};