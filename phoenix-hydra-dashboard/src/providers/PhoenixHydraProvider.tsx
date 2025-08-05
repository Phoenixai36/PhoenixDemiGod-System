import React, { createContext, ReactNode, useContext, useEffect } from 'react';
import { usePhoenixHydraStore } from '../stores/phoenixHydraStore';

interface PhoenixHydraContextType {
  isConnected: boolean;
  connectionStatus: string;
  reconnect: () => void;
}

const PhoenixHydraContext = createContext<PhoenixHydraContextType | undefined>(undefined);

interface PhoenixHydraProviderProps {
  children: ReactNode;
}

export const PhoenixHydraProvider: React.FC<PhoenixHydraProviderProps> = ({ children }) => {
  const { connectionStatus, initializeConnection } = usePhoenixHydraStore();

  useEffect(() => {
    // Initialize connection on mount
    initializeConnection();
  }, [initializeConnection]);

  const contextValue: PhoenixHydraContextType = {
    isConnected: connectionStatus === 'connected',
    connectionStatus,
    reconnect: initializeConnection
  };

  return (
    <PhoenixHydraContext.Provider value={contextValue}>
      {children}
    </PhoenixHydraContext.Provider>
  );
};

export const usePhoenixHydra = () => {
  const context = useContext(PhoenixHydraContext);
  if (context === undefined) {
    throw new Error('usePhoenixHydra must be used within a PhoenixHydraProvider');
  }
  return context;
};