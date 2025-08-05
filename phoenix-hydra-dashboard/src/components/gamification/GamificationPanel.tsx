import { motion } from 'framer-motion';
import { Star, Target, TrendingUp, Trophy, Zap } from 'lucide-react';
import React from 'react';
import { useGamificationStore } from '../../stores/gamificationStore';

const GamificationPanel: React.FC = () => {
  const {
    currentLevel,
    currentXP,
    xpToNextLevel,
    unlockedAchievements,
    userStats
  } = useGamificationStore();

  const xpProgress = ((currentXP / (currentXP + xpToNextLevel)) * 100);

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.8, delay: 0.6 }}
      className="absolute bottom-4 left-4 right-4"
    >
      <div className="glass-dark p-4 rounded-lg border border-border/50">
        {/* Level and XP */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-accent to-primary rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-bold">{currentLevel}</span>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-foreground">
                  AI Master Level {currentLevel}
                </h3>
                <p className="text-xs text-muted-foreground">
                  {currentXP} XP • {xpToNextLevel} to next level
                </p>
              </div>
            </div>
            <Zap size={16} className="text-accent" />
          </div>
          
          {/* XP Progress Bar */}
          <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
            <motion.div
              className="xp-bar h-full rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${xpProgress}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
            />
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-1 mb-1">
              <Trophy size={14} className="text-accent" />
              <span className="text-xs text-muted-foreground">Achievements</span>
            </div>
            <span className="text-lg font-bold text-foreground">
              {unlockedAchievements.length}
            </span>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center space-x-1 mb-1">
              <Target size={14} className="text-primary" />
              <span className="text-xs text-muted-foreground">Messages</span>
            </div>
            <span className="text-lg font-bold text-foreground">
              {userStats.totalMessages}
            </span>
          </div>
        </div>

        {/* Recent Achievements */}
        {unlockedAchievements.length > 0 && (
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <Star size={14} className="text-accent" />
              <span className="text-xs text-muted-foreground">Recent Achievements</span>
            </div>
            <div className="flex space-x-1">
              {unlockedAchievements.slice(-3).map((achievement) => (
                <motion.div
                  key={achievement.id}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="w-8 h-8 bg-gradient-to-br from-accent to-primary rounded-full flex items-center justify-center text-sm"
                  title={achievement.name}
                >
                  {achievement.icon}
                </motion.div>
              ))}
              {unlockedAchievements.length > 3 && (
                <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center text-xs text-muted-foreground">
                  +{unlockedAchievements.length - 3}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Streak Indicator */}
        {userStats.streak > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-3 flex items-center justify-center space-x-2 bg-gradient-to-r from-accent/20 to-primary/20 rounded-lg p-2"
          >
            <TrendingUp size={14} className="text-accent" />
            <span className="text-xs text-foreground">
              🔥 {userStats.streak} day streak!
            </span>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default GamificationPanel;