import { AnimatePresence, motion } from "framer-motion";
import React, { useEffect, useState } from "react";
import { BrowserRouter as Router } from "react-router-dom";

// Core Components
import Character3D from "./components/character/Character3D";
import ChatInterface from "./components/chat/ChatInterface";
import GamificationPanel from "./components/gamification/GamificationPanel";
import DashboardLayout from "./components/layout/DashboardLayout";
import SystemMonitor from "./components/monitoring/SystemMonitor";

// Providers and Stores
import { GamificationProvider } from "./providers/GamificationProvider";
import { PhoenixHydraProvider } from "./providers/PhoenixHydraProvider";
import { useGamificationStore } from "./stores/gamificationStore";
import { usePhoenixHydraStore } from "./stores/phoenixHydraStore";

// Effects and Animations
import ParticleBackground from "./components/effects/ParticleBackground";
import AchievementNotifications from "./components/gamification/AchievementNotifications";
import LevelUpEffect from "./components/gamification/LevelUpEffect";

// Styles
import "./App.css";

const App: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [currentView, setCurrentView] = useState<
    "chat" | "monitor" | "settings"
  >("chat");

  // Initialize stores
  const { connectionStatus, initializeConnection } = usePhoenixHydraStore();
  const { currentLevel, showLevelUpEffect } = useGamificationStore();

  useEffect(() => {
    // Initialize Phoenix Hydra connection
    const initializeApp = async () => {
      try {
        await initializeConnection();
        setIsLoading(false);
      } catch (error) {
        console.error("Failed to initialize Phoenix Hydra connection:", error);
        setIsLoading(false);
      }
    };

    initializeApp();
  }, [initializeConnection]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-foreground mb-2">
            Phoenix Hydra
          </h2>
          <p className="text-muted-foreground">Initializing AI Dashboard...</p>
        </motion.div>
      </div>
    );
  }

  return (
    <PhoenixHydraProvider>
      <GamificationProvider>
        <Router>
          <div className="min-h-screen bg-background text-foreground overflow-hidden">
            {/* Particle Background */}
            <ParticleBackground />

            {/* Main Dashboard Layout */}
            <DashboardLayout>
              <div className="flex h-full">
                {/* Left Panel - 3D Character */}
                <motion.div
                  initial={{ x: -100, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                  className="w-1/3 min-w-[400px] relative"
                >
                  <Character3D />
                  <GamificationPanel />
                </motion.div>

                {/* Center Panel - Chat Interface */}
                <motion.div
                  initial={{ y: 50, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
                  className="flex-1 flex flex-col"
                >
                  <AnimatePresence mode="wait">
                    {currentView === "chat" && (
                      <motion.div
                        key="chat"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.3 }}
                        className="h-full"
                      >
                        <ChatInterface />
                      </motion.div>
                    )}

                    {currentView === "monitor" && (
                      <motion.div
                        key="monitor"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.3 }}
                        className="h-full"
                      >
                        <SystemMonitor />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>

                {/* Right Panel - System Status */}
                <motion.div
                  initial={{ x: 100, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ duration: 0.8, delay: 0.4, ease: "easeOut" }}
                  className="w-80 border-l border-border"
                >
                  <div className="p-6 h-full">
                    <h3 className="text-lg font-semibold mb-4 text-foreground">
                      System Status
                    </h3>

                    {/* Connection Status */}
                    <div className="mb-6">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-muted-foreground">
                          Phoenix Hydra
                        </span>
                        <div
                          className={`w-3 h-3 rounded-full ${
                            connectionStatus === "connected"
                              ? "bg-success animate-pulse"
                              : connectionStatus === "connecting"
                              ? "bg-warning animate-pulse"
                              : "bg-error"
                          }`}
                        />
                      </div>
                      <p className="text-xs text-muted-foreground capitalize">
                        {connectionStatus}
                      </p>
                    </div>

                    {/* Quick Actions */}
                    <div className="space-y-2 mb-6">
                      <button
                        onClick={() => setCurrentView("chat")}
                        className={`w-full p-3 rounded-lg text-left transition-all duration-200 ${
                          currentView === "chat"
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted hover:bg-muted/80 text-muted-foreground"
                        }`}
                      >
                        💬 Chat Interface
                      </button>
                      <button
                        onClick={() => setCurrentView("monitor")}
                        className={`w-full p-3 rounded-lg text-left transition-all duration-200 ${
                          currentView === "monitor"
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted hover:bg-muted/80 text-muted-foreground"
                        }`}
                      >
                        📊 System Monitor
                      </button>
                    </div>

                    {/* Level Progress */}
                    <div className="mb-6">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-muted-foreground">
                          Level {currentLevel}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          AI Mastery
                        </span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-2">
                        <motion.div
                          className="xp-bar h-2 rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: "65%" }}
                          transition={{ duration: 1, delay: 1 }}
                        />
                      </div>
                    </div>
                  </div>
                </motion.div>
              </div>
            </DashboardLayout>

            {/* Global Effects */}
            <AchievementNotifications />
            <AnimatePresence>
              {showLevelUpEffect && <LevelUpEffect key="levelup" />}
            </AnimatePresence>
          </div>
        </Router>
      </GamificationProvider>
    </PhoenixHydraProvider>
  );
};

export default App;
