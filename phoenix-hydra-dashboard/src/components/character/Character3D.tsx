import React, { useRef, useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Spline from '@splinetool/react-spline';
import { useGamificationStore } from '../../stores/gamificationStore';
import { usePhoenixHydraStore } from '../../stores/phoenixHydraStore';
import { AnimationController } from '../../utils/AnimationController';
import { PersonalityEngine } from '../../utils/PersonalityEngine';

// Character customization options
interface CharacterCustomization {
  theme: 'default' | 'cyberpunk' | 'retro' | 'minimal';
  accessories: string[];
  colors: {
    primary: string;
    secondary: string;
    accent: string;
  };
}

const Character3D: React.FC = () => {
  const splineRef = useRef<any>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInteracting, setIsInteracting] = useState(false);
  const [currentAnimation, setCurrentAnimation] = useState<string>('idle');
  const [speechBubble, setSpeechBubble] = useState<string | null>(null);
  const [customization, setCustomization] = useState<CharacterCustomization>({
    theme: 'default',
    accessories: ['glasses', 'hoodie'],
    colors: {
      primary: '#3b82f6',
      secondary: '#8b5cf6',
      accent: '#f59e0b'
    }
  });

  // Store hooks
  const { currentLevel, currentXP, achievements } = useGamificationStore();
  const { lastMessage, isTyping } = usePhoenixHydraStore();

  // Animation and personality controllers
  const animationController = useRef(new AnimationController());
  const personalityEngine = useRef(new PersonalityEngine());

  // Spline scene URL - Replace with your actual Spline scene
  const splineSceneUrl = "https://prod.spline.design/your-nerdy-robot-scene-id/scene.splinecode";

  // Handle Spline load
  const onLoad = useCallback((spline: any) => {
    splineRef.current = spline;
    setIsLoaded(true);
    
    // Initialize character with idle animation
    animationController.current.playAnimation('idle');
    
    console.log('3D Character loaded successfully');
  }, []);

  // Handle character interactions
  const handleCharacterClick = useCallback((e: any) => {
    if (!isLoaded) return;
    
    setIsInteracting(true);
    
    // Get random personality response
    const response = personalityEngine.current.getRandomResponse('greeting');
    setSpeechBubble(response);
    
    // Play interaction animation
    animationController.current.playAnimation('wave');
    
    // Clear speech bubble after 3 seconds
    setTimeout(() => {
      setSpeechBubble(null);
      setIsInteracting(false);
      animationController.current.playAnimation('idle');
    }, 3000);
  }, [isLoaded]);

  // React to chat messages
  useEffect(() => {
    if (lastMessage && isLoaded) {
      const messageType = lastMessage.type;
      const content = lastMessage.content;
      
      // Determine animation based on message content
      let animation = 'thinking';
      let response = '';
      
      if (content.includes('error') || content.includes('failed')) {
        animation = 'confused';
        response = personalityEngine.current.getRandomResponse('error');
      } else if (content.includes('success') || content.includes('completed')) {
        animation = 'celebrate';
        response = personalityEngine.current.getRandomResponse('success');
      } else if (content.includes('code') || content.includes('programming')) {
        animation = 'coding';
        response = personalityEngine.current.getRandomResponse('coding');
      } else {
        response = personalityEngine.current.getRandomResponse('general');
      }
      
      // Play animation and show response
      animationController.current.playAnimation(animation);
      setSpeechBubble(response);
      
      // Return to idle after animation
      setTimeout(() => {
        setSpeechBubble(null);
        animationController.current.playAnimation('idle');
      }, 4000);
    }
  }, [lastMessage, isLoaded]);

  // React to typing indicator
  useEffect(() => {
    if (isTyping && isLoaded) {
      animationController.current.playAnimation('listening');
      setSpeechBubble("I'm listening... 🤔");
    } else if (!isTyping && speechBubble === "I'm listening... 🤔") {
      setSpeechBubble(null);
      animationController.current.playAnimation('idle');
    }
  }, [isTyping, isLoaded, speechBubble]);

  // Level up celebration
  useEffect(() => {
    if (currentLevel > 1 && isLoaded) {
      animationController.current.playAnimation('levelup');
      setSpeechBubble(`🎉 Level ${currentLevel}! You're becoming an AI master!`);
      
      setTimeout(() => {
        setSpeechBubble(null);
        animationController.current.playAnimation('idle');
      }, 5000);
    }
  }, [currentLevel, isLoaded]);

  return (
    <div className="relative h-full w-full">
      {/* 3D Character Container */}
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1, ease: "easeOut" }}
        className="relative h-full w-full perspective-1000"
      >
        {/* Loading State */}
        {!isLoaded && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/50 backdrop-blur-sm rounded-lg">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full"
            />
            <div className="ml-4">
              <p className="text-foreground font-medium">Loading AI Character...</p>
              <p className="text-muted-foreground text-sm">Initializing personality matrix</p>
            </div>
          </div>
        )}

        {/* Spline 3D Scene */}
        <div 
          className="h-full w-full cursor-pointer"
          onClick={handleCharacterClick}
        >
          <Spline
            scene={splineSceneUrl}
            onLoad={onLoad}
            style={{
              width: '100%',
              height: '100%',
              background: 'transparent'
            }}
          />
        </div>

        {/* Character Interaction Overlay */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: isInteracting ? 1 : 0 }}
          className="absolute inset-0 bg-primary/10 rounded-lg pointer-events-none"
        />

        {/* Speech Bubble */}
        <AnimatePresence>
          {speechBubble && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.8, y: -20 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="absolute top-4 left-4 right-4 z-10"
            >
              <div className="glass-dark p-4 rounded-2xl border border-primary/30">
                <p className="text-foreground text-sm leading-relaxed">
                  {speechBubble}
                </p>
                {/* Speech bubble tail */}
                <div className="absolute bottom-0 left-8 transform translate-y-full">
                  <div className="w-0 h-0 border-l-8 border-r-8 border-t-8 border-l-transparent border-r-transparent border-t-muted" />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Character Status Indicators */}
        <div className="absolute bottom-4 left-4 right-4">
          <div className="glass-dark p-3 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-muted-foreground">AI Companion</span>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-success rounded-full animate-pulse" />
                <span className="text-xs text-success">Active</span>
              </div>
            </div>
            
            {/* Mood Indicator */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Mood</span>
              <span className="text-xs text-foreground">
                {isInteracting ? '😊 Engaged' : isTyping ? '🤔 Thinking' : '😎 Chill'}
              </span>
            </div>
          </div>
        </div>

        {/* Character Customization Panel */}
        <motion.div
          initial={{ x: -100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="absolute top-4 right-4"
        >
          <div className="glass-dark p-2 rounded-lg">
            <button
              className="p-2 text-muted-foreground hover:text-foreground transition-colors duration-200"
              title="Customize Character"
            >
              🎨
            </button>
          </div>
        </motion.div>

        {/* Achievement Showcase */}
        {achievements.length > 0 && (
          <motion.div
            initial={{ y: 100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, delay: 1 }}
            className="absolute bottom-20 right-4"
          >
            <div className="glass-dark p-2 rounded-lg">
              <div className="flex space-x-1">
                {achievements.slice(0, 3).map((achievement, index) => (
                  <motion.div
                    key={achievement.id}
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                    className="w-8 h-8 bg-gradient-to-br from-accent to-primary rounded-full flex items-center justify-center text-xs"
                    title={achievement.name}
                  >
                    {achievement.icon}
                  </motion.div>
                ))}
                {achievements.length > 3 && (
                  <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center text-xs text-muted-foreground">
                    +{achievements.length - 3}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {/* Interaction Hints */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: isLoaded && !isInteracting ? 1 : 0 }}
          transition={{ duration: 0.5 }}
          className="absolute bottom-4 left-1/2 transform -translate-x-1/2"
        >
          <div className="glass-dark px-3 py-1 rounded-full">
            <p className="text-xs text-muted-foreground">Click me to interact! 👋</p>
          </div>
        </motion.div>
      </div>

      {/* Character Stats Overlay */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8, delay: 0.3 }}
        className="absolute top-0 left-0 p-4"
      >
        <div className="glass-dark p-3 rounded-lg min-w-[200px]">
          <h3 className="text-sm font-semibold text-foreground mb-2">
            🤖 Nerdy AI Companion
          </h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Level</span>
              <span className="text-primary font-medium">{currentLevel}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">XP</span>
              <span className="text-accent font-medium">{currentXP}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Achievements</span>
              <span className="text-success font-medium">{achievements.length}</span>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Character3D;