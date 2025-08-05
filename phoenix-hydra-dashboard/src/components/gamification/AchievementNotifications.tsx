import { AnimatePresence, motion } from 'framer-motion';
import { Trophy, X } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { useGamificationStore } from '../../stores/gamificationStore';

const AchievementNotifications: React.FC = () => {
  const { recentAchievement } = useGamificationStore();
  const [showNotification, setShowNotification] = useState(false);

  useEffect(() => {
    if (recentAchievement) {
      setShowNotification(true);
      
      // Auto-hide after 5 seconds
      const timer = setTimeout(() => {
        setShowNotification(false);
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [recentAchievement]);

  if (!recentAchievement) return null;

  const getRarityColor = (rarity: string) => {
    switch (rarity) {
      case 'legendary':
        return 'from-yellow-400 to-orange-500';
      case 'epic':
        return 'from-purple-400 to-pink-500';
      case 'rare':
        return 'from-blue-400 to-cyan-500';
      default:
        return 'from-gray-400 to-gray-600';
    }
  };

  const getRarityGlow = (rarity: string) => {
    switch (rarity) {
      case 'legendary':
        return 'shadow-yellow-500/50';
      case 'epic':
        return 'shadow-purple-500/50';
      case 'rare':
        return 'shadow-blue-500/50';
      default:
        return 'shadow-gray-500/50';
    }
  };

  return (
    <AnimatePresence>
      {showNotification && (
        <motion.div
          initial={{ opacity: 0, x: 400, scale: 0.8 }}
          animate={{ opacity: 1, x: 0, scale: 1 }}
          exit={{ opacity: 0, x: 400, scale: 0.8 }}
          transition={{ 
            type: "spring", 
            stiffness: 300, 
            damping: 30 
          }}
          className="achievement-popup"
        >
          <div className={`
            glass-dark border-2 border-accent/50 rounded-lg p-4 min-w-[300px] max-w-[400px]
            shadow-2xl ${getRarityGlow(recentAchievement.rarity)}
          `}>
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Trophy size={20} className="text-accent" />
                <span className="text-sm font-semibold text-foreground">
                  Achievement Unlocked!
                </span>
              </div>
              <button
                onClick={() => setShowNotification(false)}
                className="text-muted-foreground hover:text-foreground transition-colors duration-200"
              >
                <X size={16} />
              </button>
            </div>

            {/* Achievement Content */}
            <div className="flex items-start space-x-3">
              {/* Achievement Icon */}
              <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ delay: 0.2, type: "spring", stiffness: 300 }}
                className={`
                  w-16 h-16 rounded-full flex items-center justify-center text-2xl
                  bg-gradient-to-br ${getRarityColor(recentAchievement.rarity)}
                  shadow-lg
                `}
              >
                {recentAchievement.icon}
              </motion.div>

              {/* Achievement Details */}
              <div className="flex-1">
                <motion.h3
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="text-lg font-bold text-foreground mb-1"
                >
                  {recentAchievement.name}
                </motion.h3>
                
                <motion.p
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  className="text-sm text-muted-foreground mb-2"
                >
                  {recentAchievement.description}
                </motion.p>

                {/* Rarity and XP */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  className="flex items-center justify-between"
                >
                  <span className={`
                    text-xs px-2 py-1 rounded-full font-medium capitalize
                    ${recentAchievement.rarity === 'legendary' ? 'bg-yellow-500/20 text-yellow-400' :
                      recentAchievement.rarity === 'epic' ? 'bg-purple-500/20 text-purple-400' :
                      recentAchievement.rarity === 'rare' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-gray-500/20 text-gray-400'}
                  `}>
                    {recentAchievement.rarity}
                  </span>
                  
                  <span className="text-xs text-accent font-semibold">
                    +{recentAchievement.xpReward} XP
                  </span>
                </motion.div>
              </div>
            </div>

            {/* Celebration Particles */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-lg">
              {[...Array(8)].map((_, i) => (
                <motion.div
                  key={i}
                  initial={{ 
                    opacity: 1, 
                    scale: 0,
                    x: '50%',
                    y: '50%'
                  }}
                  animate={{ 
                    opacity: 0, 
                    scale: 1,
                    x: `${50 + (Math.random() - 0.5) * 200}%`,
                    y: `${50 + (Math.random() - 0.5) * 200}%`
                  }}
                  transition={{ 
                    duration: 2, 
                    delay: i * 0.1,
                    ease: "easeOut"
                  }}
                  className="absolute w-2 h-2 bg-accent rounded-full"
                />
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default AchievementNotifications;