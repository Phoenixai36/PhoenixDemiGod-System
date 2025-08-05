import { motion } from 'framer-motion';
import {
    Activity,
    AlertTriangle,
    CheckCircle,
    Cpu,
    HardDrive,
    Memory,
    Network,
    Play,
    RotateCcw,
    Square
} from 'lucide-react';
import React, { useState } from 'react';
import { usePhoenixHydraStore } from '../../stores/phoenixHydraStore';

const SystemMonitor: React.FC = () => {
  const { containers, systemMetrics, logs, executeCommand } = usePhoenixHydraStore();
  const [selectedContainer, setSelectedContainer] = useState<string | null>(null);

  // Mock system metrics if not available
  const mockMetrics = {
    cpu: 45,
    memory: 68,
    disk: 32,
    network: { in: 1.2, out: 0.8 },
    timestamp: new Date()
  };

  const metrics = systemMetrics || mockMetrics;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'text-success';
      case 'stopped':
        return 'text-muted-foreground';
      case 'error':
        return 'text-error';
      case 'starting':
        return 'text-warning';
      default:
        return 'text-muted-foreground';
    }
  };

  const getHealthIcon = (health: string) => {
    switch (health) {
      case 'healthy':
        return <CheckCircle size={16} className="text-success" />;
      case 'unhealthy':
        return <AlertTriangle size={16} className="text-error" />;
      default:
        return <Activity size={16} className="text-muted-foreground" />;
    }
  };

  const handleContainerAction = (containerName: string, action: string) => {
    executeCommand(`/container ${action} ${containerName}`);
  };

  return (
    <div className="h-full p-6 space-y-6">
      {/* System Metrics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        {/* CPU Usage */}
        <div className="glass-dark p-4 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Cpu size={20} className="text-primary" />
              <span className="text-sm font-medium text-foreground">CPU</span>
            </div>
            <span className="text-lg font-bold text-foreground">{metrics.cpu}%</span>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <motion.div
              className="bg-gradient-to-r from-primary to-secondary h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${metrics.cpu}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
            />
          </div>
        </div>

        {/* Memory Usage */}
        <div className="glass-dark p-4 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Memory size={20} className="text-accent" />
              <span className="text-sm font-medium text-foreground">Memory</span>
            </div>
            <span className="text-lg font-bold text-foreground">{metrics.memory}%</span>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <motion.div
              className="bg-gradient-to-r from-accent to-warning h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${metrics.memory}%` }}
              transition={{ duration: 1, delay: 0.2, ease: "easeOut" }}
            />
          </div>
        </div>

        {/* Disk Usage */}
        <div className="glass-dark p-4 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <HardDrive size={20} className="text-success" />
              <span className="text-sm font-medium text-foreground">Disk</span>
            </div>
            <span className="text-lg font-bold text-foreground">{metrics.disk}%</span>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <motion.div
              className="bg-gradient-to-r from-success to-primary h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${metrics.disk}%` }}
              transition={{ duration: 1, delay: 0.4, ease: "easeOut" }}
            />
          </div>
        </div>

        {/* Network */}
        <div className="glass-dark p-4 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Network size={20} className="text-secondary" />
              <span className="text-sm font-medium text-foreground">Network</span>
            </div>
          </div>
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">↓ In</span>
              <span className="text-foreground">{metrics.network.in} MB/s</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">↑ Out</span>
              <span className="text-foreground">{metrics.network.out} MB/s</span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Container Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass-dark p-6 rounded-lg"
      >
        <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center space-x-2">
          <Activity size={20} className="text-primary" />
          <span>Phoenix Hydra Containers</span>
        </h3>

        <div className="space-y-3">
          {containers.map((container, index) => (
            <motion.div
              key={container.name}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center justify-between p-4 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors duration-200"
            >
              <div className="flex items-center space-x-4">
                {getHealthIcon(container.health)}
                <div>
                  <h4 className="font-medium text-foreground">{container.name}</h4>
                  <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                    <span className={`capitalize ${getStatusColor(container.status)}`}>
                      {container.status}
                    </span>
                    <span>CPU: {container.cpu}%</span>
                    <span>Memory: {container.memory}MB</span>
                    <span>Uptime: {container.uptime}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                {container.status === 'running' ? (
                  <>
                    <button
                      onClick={() => handleContainerAction(container.name, 'restart')}
                      className="p-2 text-warning hover:bg-warning/20 rounded-lg transition-colors duration-200"
                      title="Restart Container"
                    >
                      <RotateCcw size={16} />
                    </button>
                    <button
                      onClick={() => handleContainerAction(container.name, 'stop')}
                      className="p-2 text-error hover:bg-error/20 rounded-lg transition-colors duration-200"
                      title="Stop Container"
                    >
                      <Square size={16} />
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => handleContainerAction(container.name, 'start')}
                    className="p-2 text-success hover:bg-success/20 rounded-lg transition-colors duration-200"
                    title="Start Container"
                  >
                    <Play size={16} />
                  </button>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* System Logs */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="glass-dark p-6 rounded-lg"
      >
        <h3 className="text-lg font-semibold text-foreground mb-4">
          System Logs
        </h3>
        
        <div className="bg-black/50 rounded-lg p-4 h-64 overflow-y-auto custom-scrollbar font-mono text-sm">
          {logs.length > 0 ? (
            logs.map((log, index) => (
              <div key={index} className="text-green-400 mb-1">
                {log}
              </div>
            ))
          ) : (
            <div className="text-muted-foreground">
              No logs available. Connect to Phoenix Hydra to see system logs.
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default SystemMonitor;