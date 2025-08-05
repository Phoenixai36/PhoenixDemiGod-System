import { motion } from 'framer-motion';
import React, { useEffect } from 'react';
import { useGamificationStore } from '../../stores/gamificationStore';

const LevelUpEffect: React.FC = () => {
  const { currentLevel, setShowLevelUpEffect } = useGamificationStore();

  useEffect(() => {
    // Auto-hide after animation completes
    const timer = setTimeout(() => {
      setShowLevelUpEffect(false);
    }, 3000);

    return () => clearTimeout(timer);
  }, [setShowLevelUpEffect]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="level-up-effect"
    >
      {/* Background Pulse */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ 
          scale: [0.8, 1.2, 1],
          opacity: [0, 0.8, 0]
        }}
        transition={{ 
          duration: 2,
          times: [0, 0.5, 1],
          ease: "easeOut"
        }}
        className="absolute inset-0 bg-gradient-radial from-primary/30 via-primary/10 to-transparent"
      />

      {/* Level Up Text */}
      <div className="absolute inset-0 flex items-center justify-center">
        <motion.div
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ 
            type: "spring",
            stiffness: 300,
            damping: 20,
            delay: 0.2
          }}
          className="text-center"
        >
          <motion.h1
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.8 }}
            className="text-6xl font-bold text-primary neon-text mb-4"
          >
            LEVEL UP!
          </motion.h1>
          
          <motion.div
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.8, duration: 0.5 }}
            className="flex items-center justify-center space-x-4"
          >
            <div className="w-16 h-16 bg-gradient-to-br from-accent to-primary rounded-full flex items-center justify-center shadow-2xl">
              <span className="text-white text-2xl font-bold">{currentLevel}</span>
            </div>
            <div className="text-left">
              <p className="text-2xl font-semibold text-foreground">
                Level {currentLevel}
              </p>
              <p className="text-lg text-muted-foreground">
                AI Master Achieved!
              </p>
            </div>
          </motion.div>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.2, duration: 0.6 }}
            className="text-xl text-muted-foreground mt-6"
          >
            🎉 You're becoming a true Phoenix Hydra expert!
          </motion.p>
        </motion.div>
      </div>

      {/* Floating Particles */}
      <div className="absolute inset-0 pointer-events-none">
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            initial={{ 
              opacity: 0,
              scale: 0,
              x: '50%',
              y: '50%'
            }}
            animate={{ 
              opacity: [0, 1, 0],
              scale: [0, 1, 0],
              x: `${Math.random() * 100}%`,
              y: `${Math.random() * 100}%`
            }}
            transition={{ 
              duration: 3,
              delay: Math.random() * 2,
              ease: "easeOut"
            }}
            className="absolute w-4 h-4 bg-gradient-to-br from-accent to-primary rounded-full"
          />
        ))}
      </div>

      {/* Confetti */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {[...Array(50)].map((_, i) => (
          <motion.div
            key={`confetti-${i}`}
            initial={{ 
              opacity: 1,
              y: -100,
              x: `${Math.random() * 100}%`,
              rotate: 0
            }}
            animate={{ 
              opacity: 0,
              y: window.innerHeight + 100,
              rotate: 360 * (Math.random() > 0.5 ? 1 : -1)
            }}
            transition={{ 
              duration: 3 + Math.random() * 2,
              delay: Math.random() * 1,
              ease: "easeOut"
            }}
            className={`
              absolute w-3 h-3 
              ${Math.random() > 0.5 ? 'bg-accent' : 'bg-primary'}
              ${Math.random() > 0.5 ? 'rounded-full' : 'rounded-sm'}
            `}
          />
        ))}
      </div>

      {/* Radial Burst */}
      <motion.div
        initial={{ scale: 0, opacity: 1 }}
        animate={{ scale: 3, opacity: 0 }}
        transition={{ duration: 1.5, ease: "easeOut" }}
        className="absolute inset-0 flex items-center justify-center"
      >
        <div className="w-32 h-32 border-4 border-primary rounded-full" />
      </motion.div>
    </motion.div>
  );
};

export default LevelUpEffect;