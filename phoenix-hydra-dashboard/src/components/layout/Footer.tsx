import { motion } from 'framer-motion';
import { Cpu, Heart, Shield, Zap } from 'lucide-react';
import React from 'react';

const Footer: React.FC = () => {
  const systemStats = [
    { icon: Cpu, label: 'CPU', value: '45%', color: 'text-success' },
    { icon: Zap, label: 'Memory', value: '2.1GB', color: 'text-warning' },
    { icon: Shield, label: 'Security', value: 'Active', color: 'text-primary' },
  ];

  return (
    <footer className="glass-dark border-t border-border/50 backdrop-blur-xl">
      <div className="container mx-auto px-6 py-3">
        <div className="flex items-center justify-between">
          {/* System Stats */}
          <div className="flex items-center space-x-6">
            {systemStats.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="flex items-center space-x-2"
              >
                <stat.icon size={16} className={`${stat.color}`} />
                <span className="text-xs text-muted-foreground">
                  {stat.label}: <span className={stat.color}>{stat.value}</span>
                </span>
              </motion.div>
            ))}
          </div>

          {/* Status Indicator */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex items-center space-x-2"
          >
            <div className="w-2 h-2 bg-success rounded-full animate-pulse" />
            <span className="text-xs text-muted-foreground">All systems operational</span>
          </motion.div>

          {/* Copyright */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="flex items-center space-x-1 text-xs text-muted-foreground"
          >
            <span>Made with</span>
            <Heart size={12} className="text-error animate-pulse" />
            <span>by Phoenix Hydra</span>
          </motion.div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;