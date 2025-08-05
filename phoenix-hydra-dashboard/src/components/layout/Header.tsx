import { motion } from 'framer-motion';
import { Bell, Menu, Settings, User, X } from 'lucide-react';
import React, { useState } from 'react';

const Header: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [notifications, setNotifications] = useState(3);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  return (
    <header className="glass-dark border-b border-border/50 backdrop-blur-xl">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="flex items-center space-x-3"
          >
            <div className="w-10 h-10 bg-gradient-to-br from-primary to-secondary rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">PH</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">Phoenix Hydra</h1>
              <p className="text-xs text-muted-foreground">AI Dashboard</p>
            </div>
          </motion.div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            <motion.a
              href="#chat"
              className="text-muted-foreground hover:text-foreground transition-colors duration-200"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Chat
            </motion.a>
            <motion.a
              href="#monitor"
              className="text-muted-foreground hover:text-foreground transition-colors duration-200"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Monitor
            </motion.a>
            <motion.a
              href="#analytics"
              className="text-muted-foreground hover:text-foreground transition-colors duration-200"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Analytics
            </motion.a>
            <motion.a
              href="#settings"
              className="text-muted-foreground hover:text-foreground transition-colors duration-200"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Settings
            </motion.a>
          </nav>

          {/* User Actions */}
          <div className="flex items-center space-x-4">
            {/* Notifications */}
            <motion.button
              className="relative p-2 text-muted-foreground hover:text-foreground transition-colors duration-200"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <Bell size={20} />
              {notifications > 0 && (
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-1 -right-1 w-5 h-5 bg-error text-error-foreground text-xs rounded-full flex items-center justify-center"
                >
                  {notifications}
                </motion.span>
              )}
            </motion.button>

            {/* Settings */}
            <motion.button
              className="p-2 text-muted-foreground hover:text-foreground transition-colors duration-200"
              whileHover={{ scale: 1.1, rotate: 90 }}
              whileTap={{ scale: 0.9 }}
            >
              <Settings size={20} />
            </motion.button>

            {/* User Profile */}
            <motion.button
              className="flex items-center space-x-2 p-2 rounded-lg hover:bg-muted/50 transition-colors duration-200"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <div className="w-8 h-8 bg-gradient-to-br from-accent to-primary rounded-full flex items-center justify-center">
                <User size={16} className="text-white" />
              </div>
              <span className="hidden md:block text-sm text-foreground">AI Master</span>
            </motion.button>

            {/* Mobile Menu Toggle */}
            <motion.button
              className="md:hidden p-2 text-muted-foreground hover:text-foreground"
              onClick={toggleMenu}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </motion.button>
          </div>
        </div>

        {/* Mobile Navigation */}
        <motion.nav
          initial={false}
          animate={{
            height: isMenuOpen ? 'auto' : 0,
            opacity: isMenuOpen ? 1 : 0,
          }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className="md:hidden overflow-hidden"
        >
          <div className="py-4 space-y-2">
            <a
              href="#chat"
              className="block py-2 px-4 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors duration-200"
            >
              💬 Chat Interface
            </a>
            <a
              href="#monitor"
              className="block py-2 px-4 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors duration-200"
            >
              📊 System Monitor
            </a>
            <a
              href="#analytics"
              className="block py-2 px-4 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors duration-200"
            >
              📈 Analytics
            </a>
            <a
              href="#settings"
              className="block py-2 px-4 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors duration-200"
            >
              ⚙️ Settings
            </a>
          </div>
        </motion.nav>
      </div>
    </header>
  );
};

export default Header;