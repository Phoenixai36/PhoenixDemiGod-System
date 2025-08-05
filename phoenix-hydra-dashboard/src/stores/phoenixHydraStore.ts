import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

export interface ChatMessage {
  id: string;
  type: 'user' | 'bot' | 'system' | 'error';
  content: string;
  timestamp: Date;
  metadata?: {
    command?: string;
    duration?: number;
    status?: 'success' | 'error' | 'pending';
  };
}

export interface ContainerStatus {
  name: string;
  status: 'running' | 'stopped' | 'error' | 'starting';
  cpu: number;
  memory: number;
  uptime: string;
  health: 'healthy' | 'unhealthy' | 'unknown';
}

export interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  network: {
    in: number;
    out: number;
  };
  timestamp: Date;
}

export interface PhoenixHydraState {
  // Connection
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error';
  websocket: WebSocket | null;
  reconnectAttempts: number;
  maxReconnectAttempts: number;
  
  // Chat
  messages: ChatMessage[];
  isTyping: boolean;
  lastMessage: ChatMessage | null;
  
  // System Status
  containers: ContainerStatus[];
  systemMetrics: SystemMetrics | null;
  logs: string[];
  
  // Actions
  initializeConnection: () => Promise<void>;
  disconnect: () => void;
  sendMessage: (content: string, type?: 'user' | 'command') => void;
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  setTyping: (typing: boolean) => void;
  updateContainerStatus: (containers: ContainerStatus[]) => void;
  updateSystemMetrics: (metrics: SystemMetrics) => void;
  addLog: (log: string) => void;
  clearLogs: () => void;
  executeCommand: (command: string) => Promise<void>;
}

export const usePhoenixHydraStore = create<PhoenixHydraState>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    connectionStatus: 'disconnected',
    websocket: null,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,
    
    messages: [],
    isTyping: false,
    lastMessage: null,
    
    containers: [
      {
        name: 'phoenix-hydra_phoenix-core_1',
        status: 'running',
        cpu: 45,
        memory: 512,
        uptime: '2h 15m',
        health: 'healthy'
      },
      {
        name: 'phoenix-hydra_n8n-phoenix_1',
        status: 'running',
        cpu: 23,
        memory: 256,
        uptime: '2h 15m',
        health: 'healthy'
      },
      {
        name: 'phoenix-hydra_windmill-phoenix_1',
        status: 'running',
        cpu: 12,
        memory: 128,
        uptime: '2h 15m',
        health: 'healthy'
      }
    ],
    systemMetrics: null,
    logs: [],
    
    // Actions
    initializeConnection: async () => {
      const state = get();
      if (state.connectionStatus === 'connecting' || state.connectionStatus === 'connected') {
        return;
      }
      
      set({ connectionStatus: 'connecting' });
      
      try {
        // Connect to LOCAL Phoenix Hydra WebSocket
        // Using your actual Phoenix Hydra local ports
        const wsUrl = 'ws://localhost:8080/ws'; // Phoenix Core
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
          console.log('Connected to Phoenix Hydra');
          set({ 
            connectionStatus: 'connected', 
            websocket: ws, 
            reconnectAttempts: 0 
          });
          
          // Send initial handshake
          ws.send(JSON.stringify({
            type: 'handshake',
            data: { client: 'phoenix-hydra-dashboard' }
          }));
          
          // Add welcome message
          get().addMessage({
            type: 'system',
            content: '🚀 Connected to Phoenix Hydra! Ready to assist you with AI-powered automation.'
          });
        };
        
        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            handleWebSocketMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };
        
        ws.onclose = () => {
          console.log('Disconnected from Phoenix Hydra');
          set({ connectionStatus: 'disconnected', websocket: null });
          
          // Attempt reconnection
          const currentAttempts = get().reconnectAttempts;
          if (currentAttempts < get().maxReconnectAttempts) {
            setTimeout(() => {
              set({ reconnectAttempts: currentAttempts + 1 });
              get().initializeConnection();
            }, Math.pow(2, currentAttempts) * 1000); // Exponential backoff
          }
        };
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          set({ connectionStatus: 'error' });
        };
        
        set({ websocket: ws });
        
      } catch (error) {
        console.error('Failed to initialize connection:', error);
        set({ connectionStatus: 'error' });
      }
    },
    
    disconnect: () => {
      const { websocket } = get();
      if (websocket) {
        websocket.close();
      }
      set({ 
        connectionStatus: 'disconnected', 
        websocket: null, 
        reconnectAttempts: 0 
      });
    },
    
    sendMessage: (content: string, type: 'user' | 'command' = 'user') => {
      const { websocket, connectionStatus } = get();
      
      // Add user message to chat
      const userMessage: Omit<ChatMessage, 'id' | 'timestamp'> = {
        type,
        content
      };
      get().addMessage(userMessage);
      
      // Send to Phoenix Hydra if connected
      if (websocket && connectionStatus === 'connected') {
        websocket.send(JSON.stringify({
          type: 'chat_message',
          data: { content, messageType: type }
        }));
        
        // Show typing indicator
        get().setTyping(true);
      } else {
        // Simulate response if not connected
        setTimeout(() => {
          get().addMessage({
            type: 'bot',
            content: `I received your ${type}: "${content}". However, I'm not currently connected to Phoenix Hydra. Please check the connection status.`
          });
        }, 1000);
      }
    },
    
    addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
      const newMessage: ChatMessage = {
        ...message,
        id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date()
      };
      
      set(state => ({
        messages: [...state.messages, newMessage],
        lastMessage: newMessage
      }));
    },
    
    setTyping: (typing: boolean) => {
      set({ isTyping: typing });
    },
    
    updateContainerStatus: (containers: ContainerStatus[]) => {
      set({ containers });
    },
    
    updateSystemMetrics: (metrics: SystemMetrics) => {
      set({ systemMetrics: metrics });
    },
    
    addLog: (log: string) => {
      set(state => ({
        logs: [...state.logs.slice(-99), `[${new Date().toISOString()}] ${log}`]
      }));
    },
    
    clearLogs: () => {
      set({ logs: [] });
    },
    
    executeCommand: async (command: string) => {
      const { websocket, connectionStatus } = get();
      
      // Add command message
      get().addMessage({
        type: 'user',
        content: command,
        metadata: { command, status: 'pending' }
      });
      
      if (websocket && connectionStatus === 'connected') {
        // Send command to Phoenix Hydra
        websocket.send(JSON.stringify({
          type: 'execute_command',
          data: { command }
        }));
        
        get().setTyping(true);
      } else {
        // Simulate command execution
        setTimeout(() => {
          get().addMessage({
            type: 'system',
            content: `Command "${command}" would be executed, but Phoenix Hydra is not connected.`,
            metadata: { command, status: 'error' }
          });
        }, 1000);
      }
    }
  }))
);

// Handle incoming WebSocket messages
function handleWebSocketMessage(message: any) {
  const store = usePhoenixHydraStore.getState();
  
  switch (message.type) {
    case 'chat_response':
      store.setTyping(false);
      store.addMessage({
        type: 'bot',
        content: message.data.content
      });
      break;
      
    case 'command_result':
      store.setTyping(false);
      store.addMessage({
        type: 'system',
        content: message.data.output || 'Command executed successfully',
        metadata: {
          command: message.data.command,
          status: message.data.success ? 'success' : 'error',
          duration: message.data.duration
        }
      });
      break;
      
    case 'container_status':
      store.updateContainerStatus(message.data.containers);
      break;
      
    case 'system_metrics':
      store.updateSystemMetrics({
        ...message.data,
        timestamp: new Date()
      });
      break;
      
    case 'log_entry':
      store.addLog(message.data.message);
      break;
      
    case 'error':
      store.addMessage({
        type: 'error',
        content: `Error: ${message.data.message}`
      });
      break;
      
    default:
      console.log('Unknown message type:', message.type);
  }
}

// Subscribe to message changes for gamification
usePhoenixHydraStore.subscribe(
  (state) => state.messages,
  (messages) => {
    // Import gamification store dynamically to avoid circular dependency
    import('./gamificationStore').then(({ useGamificationStore }) => {
      const gamificationStore = useGamificationStore.getState();
      
      // Update stats based on new messages
      const userMessages = messages.filter(m => m.type === 'user').length;
      const commands = messages.filter(m => m.metadata?.command).length;
      const errors = messages.filter(m => m.type === 'error').length;
      const successes = messages.filter(m => m.metadata?.status === 'success').length;
      
      gamificationStore.updateStats({
        totalMessages: userMessages,
        totalCommands: commands,
        totalErrors: errors,
        totalSuccesses: successes
      });
      
      // Award XP for interactions
      const lastMessage = messages[messages.length - 1];
      if (lastMessage && lastMessage.type === 'user') {
        gamificationStore.addXP(5, 'Message sent');
      } else if (lastMessage && lastMessage.metadata?.status === 'success') {
        gamificationStore.addXP(10, 'Command executed');
      }
    });
  }
);