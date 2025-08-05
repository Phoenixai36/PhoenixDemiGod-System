import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  unlockedAt: Date | null;
  progress: number;
  maxProgress: number;
  xpReward: number;
}

export interface UserStats {
  totalMessages: number;
  totalCommands: number;
  totalErrors: number;
  totalSuccesses: number;
  sessionTime: number;
  streak: number;
  lastActive: Date;
}

export interface GamificationState {
  // User Progress
  currentLevel: number;
  currentXP: number;
  totalXP: number;
  xpToNextLevel: number;
  
  // Achievements
  achievements: Achievement[];
  unlockedAchievements: Achievement[];
  
  // Stats
  userStats: UserStats;
  
  // UI State
  showLevelUpEffect: boolean;
  recentAchievement: Achievement | null;
  
  // Actions
  addXP: (amount: number, reason?: string) => void;
  unlockAchievement: (achievementId: string) => void;
  updateStats: (statUpdate: Partial<UserStats>) => void;
  checkAchievements: () => void;
  resetProgress: () => void;
  setShowLevelUpEffect: (show: boolean) => void;
  calculateLevel: (xp: number) => number;
  getXPForLevel: (level: number) => number;
}

// Achievement definitions
const ACHIEVEMENTS: Achievement[] = [
  {
    id: 'first_message',
    name: 'Hello World',
    description: 'Send your first message to the AI',
    icon: '👋',
    rarity: 'common',
    unlockedAt: null,
    progress: 0,
    maxProgress: 1,
    xpReward: 10
  },
  {
    id: 'chat_master',
    name: 'Chat Master',
    description: 'Send 100 messages',
    icon: '💬',
    rarity: 'rare',
    unlockedAt: null,
    progress: 0,
    maxProgress: 100,
    xpReward: 100
  },
  {
    id: 'code_wizard',
    name: 'Code Wizard',
    description: 'Execute 50 system commands',
    icon: '🧙‍♂️',
    rarity: 'epic',
    unlockedAt: null,
    progress: 0,
    maxProgress: 50,
    xpReward: 200
  },
  {
    id: 'phoenix_master',
    name: 'Phoenix Master',
    description: 'Reach level 10',
    icon: '🔥',
    rarity: 'legendary',
    unlockedAt: null,
    progress: 0,
    maxProgress: 1,
    xpReward: 500
  },
  {
    id: 'streak_warrior',
    name: 'Streak Warrior',
    description: 'Maintain a 7-day streak',
    icon: '⚡',
    rarity: 'rare',
    unlockedAt: null,
    progress: 0,
    maxProgress: 7,
    xpReward: 150
  },
  {
    id: 'error_hunter',
    name: 'Error Hunter',
    description: 'Encounter and resolve 25 errors',
    icon: '🐛',
    rarity: 'rare',
    unlockedAt: null,
    progress: 0,
    maxProgress: 25,
    xpReward: 120
  },
  {
    id: 'night_owl',
    name: 'Night Owl',
    description: 'Use the system after midnight',
    icon: '🦉',
    rarity: 'common',
    unlockedAt: null,
    progress: 0,
    maxProgress: 1,
    xpReward: 25
  },
  {
    id: 'speed_demon',
    name: 'Speed Demon',
    description: 'Send 10 messages in under 1 minute',
    icon: '💨',
    rarity: 'epic',
    unlockedAt: null,
    progress: 0,
    maxProgress: 10,
    xpReward: 180
  }
];

export const useGamificationStore = create<GamificationState>()(
  persist(
    (set, get) => ({
      // Initial state
      currentLevel: 1,
      currentXP: 0,
      totalXP: 0,
      xpToNextLevel: 100,
      
      achievements: ACHIEVEMENTS.map(a => ({ ...a })),
      unlockedAchievements: [],
      
      userStats: {
        totalMessages: 0,
        totalCommands: 0,
        totalErrors: 0,
        totalSuccesses: 0,
        sessionTime: 0,
        streak: 0,
        lastActive: new Date()
      },
      
      showLevelUpEffect: false,
      recentAchievement: null,
      
      // Actions
      addXP: (amount: number, reason?: string) => {
        const state = get();
        const newTotalXP = state.totalXP + amount;
        const newLevel = state.calculateLevel(newTotalXP);
        const currentLevelXP = state.getXPForLevel(newLevel);
        const nextLevelXP = state.getXPForLevel(newLevel + 1);
        const currentXP = newTotalXP - currentLevelXP;
        const xpToNextLevel = nextLevelXP - newTotalXP;
        
        // Check for level up
        const leveledUp = newLevel > state.currentLevel;
        
        set({
          currentLevel: newLevel,
          currentXP,
          totalXP: newTotalXP,
          xpToNextLevel,
          showLevelUpEffect: leveledUp
        });
        
        // Check achievements after XP update
        setTimeout(() => get().checkAchievements(), 100);
        
        console.log(`+${amount} XP${reason ? ` (${reason})` : ''}`);
        if (leveledUp) {
          console.log(`🎉 Level up! Now level ${newLevel}`);
        }
      },
      
      unlockAchievement: (achievementId: string) => {
        const state = get();
        const achievement = state.achievements.find(a => a.id === achievementId);
        
        if (achievement && !achievement.unlockedAt) {
          const updatedAchievements = state.achievements.map(a =>
            a.id === achievementId
              ? { ...a, unlockedAt: new Date(), progress: a.maxProgress }
              : a
          );
          
          const unlockedAchievement = { ...achievement, unlockedAt: new Date() };
          
          set({
            achievements: updatedAchievements,
            unlockedAchievements: [...state.unlockedAchievements, unlockedAchievement],
            recentAchievement: unlockedAchievement
          });
          
          // Award XP for achievement
          get().addXP(achievement.xpReward, `Achievement: ${achievement.name}`);
          
          console.log(`🏆 Achievement unlocked: ${achievement.name}`);
        }
      },
      
      updateStats: (statUpdate: Partial<UserStats>) => {
        const state = get();
        set({
          userStats: {
            ...state.userStats,
            ...statUpdate,
            lastActive: new Date()
          }
        });
        
        // Check achievements after stats update
        setTimeout(() => get().checkAchievements(), 100);
      },
      
      checkAchievements: () => {
        const state = get();
        const { userStats, achievements, currentLevel } = state;
        
        achievements.forEach(achievement => {
          if (achievement.unlockedAt) return; // Already unlocked
          
          let shouldUnlock = false;
          let newProgress = achievement.progress;
          
          switch (achievement.id) {
            case 'first_message':
              newProgress = Math.min(userStats.totalMessages, 1);
              shouldUnlock = userStats.totalMessages >= 1;
              break;
              
            case 'chat_master':
              newProgress = Math.min(userStats.totalMessages, 100);
              shouldUnlock = userStats.totalMessages >= 100;
              break;
              
            case 'code_wizard':
              newProgress = Math.min(userStats.totalCommands, 50);
              shouldUnlock = userStats.totalCommands >= 50;
              break;
              
            case 'phoenix_master':
              newProgress = currentLevel >= 10 ? 1 : 0;
              shouldUnlock = currentLevel >= 10;
              break;
              
            case 'streak_warrior':
              newProgress = Math.min(userStats.streak, 7);
              shouldUnlock = userStats.streak >= 7;
              break;
              
            case 'error_hunter':
              newProgress = Math.min(userStats.totalErrors, 25);
              shouldUnlock = userStats.totalErrors >= 25;
              break;
              
            case 'night_owl':
              const hour = new Date().getHours();
              if (hour >= 0 && hour < 6) {
                newProgress = 1;
                shouldUnlock = true;
              }
              break;
              
            case 'speed_demon':
              // This would need to be tracked separately with timestamps
              // For now, we'll just check if they've sent many messages
              if (userStats.totalMessages >= 10) {
                newProgress = 10;
                shouldUnlock = true;
              }
              break;
          }
          
          // Update progress
          if (newProgress !== achievement.progress) {
            const updatedAchievements = state.achievements.map(a =>
              a.id === achievement.id ? { ...a, progress: newProgress } : a
            );
            set({ achievements: updatedAchievements });
          }
          
          // Unlock if criteria met
          if (shouldUnlock) {
            get().unlockAchievement(achievement.id);
          }
        });
      },
      
      resetProgress: () => {
        set({
          currentLevel: 1,
          currentXP: 0,
          totalXP: 0,
          xpToNextLevel: 100,
          achievements: ACHIEVEMENTS.map(a => ({ ...a, unlockedAt: null, progress: 0 })),
          unlockedAchievements: [],
          userStats: {
            totalMessages: 0,
            totalCommands: 0,
            totalErrors: 0,
            totalSuccesses: 0,
            sessionTime: 0,
            streak: 0,
            lastActive: new Date()
          },
          showLevelUpEffect: false,
          recentAchievement: null
        });
      },
      
      setShowLevelUpEffect: (show: boolean) => {
        set({ showLevelUpEffect: show });
      },
      
      calculateLevel: (xp: number) => {
        // Exponential leveling curve: level = floor(sqrt(xp / 50)) + 1
        return Math.floor(Math.sqrt(xp / 50)) + 1;
      },
      
      getXPForLevel: (level: number) => {
        // XP required for level: xp = (level - 1)^2 * 50
        return Math.pow(level - 1, 2) * 50;
      }
    }),
    {
      name: 'phoenix-hydra-gamification',
      version: 1
    }
  )
);