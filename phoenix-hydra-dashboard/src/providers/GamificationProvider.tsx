import type { ReactNode } from "react";
import React, { createContext, useContext, useEffect } from "react";
import type { Achievement, UserStats } from "../stores/gamificationStore";
import { useGamificationStore } from "../stores/gamificationStore";

interface GamificationContextType {
  currentLevel: number;
  currentXP: number;
  totalXP: number;
  xpToNextLevel: number;
  achievements: Achievement[];
  unlockedAchievements: Achievement[];
  recentAchievement: Achievement | null;
  showLevelUpEffect: boolean;
  userStats: UserStats;
  addXP: (amount: number, reason?: string) => void;
  unlockAchievement: (achievementId: string) => void;
  updateStats: (statUpdate: Partial<UserStats>) => void;
  checkAchievements: () => void;
  getProgressToNextLevel: () => number;
  setShowLevelUpEffect: (show: boolean) => void;
}

const GamificationContext = createContext<GamificationContextType | undefined>(
  undefined
);

interface GamificationProviderProps {
  children: ReactNode;
}

export const GamificationProvider: React.FC<GamificationProviderProps> = ({
  children,
}) => {
  const {
    currentLevel,
    currentXP,
    totalXP,
    xpToNextLevel,
    achievements,
    unlockedAchievements,
    recentAchievement,
    showLevelUpEffect,
    userStats,
    addXP: storeAddXP,
    unlockAchievement: storeUnlockAchievement,
    updateStats,
    checkAchievements,
    setShowLevelUpEffect,
    calculateLevel,
    getXPForLevel,
  } = useGamificationStore();

  useEffect(() => {
    // Initialize session tracking
    const sessionStart = Date.now();

    // Update last active time
    updateStats({ lastActive: new Date() });

    // Check for time-based achievements
    checkAchievements();

    // Track session time and activity
    const interval = setInterval(() => {
      const sessionTime = Math.floor((Date.now() - sessionStart) / 1000);
      updateStats({ sessionTime });

      // Check for session-based achievements
      checkAchievements();
    }, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [updateStats, checkAchievements]);

  // Enhanced XP addition with level up detection
  const addXP = (amount: number, reason?: string) => {
    const previousLevel = currentLevel;
    storeAddXP(amount, reason);

    // Check if level up occurred using the store's calculation
    const newLevel = calculateLevel(totalXP + amount);
    if (newLevel > previousLevel) {
      setShowLevelUpEffect(true);

      // Award bonus XP for level up
      setTimeout(() => {
        storeAddXP(50, `Level ${newLevel} Bonus!`);
      }, 1000);
    }
  };

  // Enhanced achievement unlocking
  const unlockAchievement = (achievementId: string) => {
    const achievement = achievements.find((a) => a.id === achievementId);
    if (achievement && !achievement.unlockedAt) {
      storeUnlockAchievement(achievementId);
    }
  };

  // Calculate progress percentage to next level
  const getProgressToNextLevel = (): number => {
    const currentLevelXP = getXPForLevel(currentLevel);
    const nextLevelXP = getXPForLevel(currentLevel + 1);
    const progressXP = totalXP - currentLevelXP;
    const levelXPRange = nextLevelXP - currentLevelXP;

    return Math.min(100, Math.max(0, (progressXP / levelXPRange) * 100));
  };

  const contextValue: GamificationContextType = {
    currentLevel,
    currentXP,
    totalXP,
    xpToNextLevel,
    achievements,
    unlockedAchievements,
    recentAchievement,
    showLevelUpEffect,
    userStats,
    addXP,
    unlockAchievement,
    updateStats,
    checkAchievements,
    getProgressToNextLevel,
    setShowLevelUpEffect,
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
    throw new Error(
      "useGamification must be used within a GamificationProvider"
    );
  }
  return context;
};
