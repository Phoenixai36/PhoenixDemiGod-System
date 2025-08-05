import { motion } from 'framer-motion';
import React, { ReactNode } from 'react';
import Footer from './Footer';
import Header from './Header';

interface DashboardLayoutProps {
  children: ReactNode;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <motion.div
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <Header />
      </motion.div>

      {/* Main Content */}
      <main className="flex-1 relative">
        <div className="h-full">
          {children}
        </div>
      </main>

      {/* Footer */}
      <motion.div
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
      >
        <Footer />
      </motion.div>
    </div>
  );
};

export default DashboardLayout;