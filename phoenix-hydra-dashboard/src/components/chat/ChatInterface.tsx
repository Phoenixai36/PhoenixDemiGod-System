import { AnimatePresence, motion } from 'framer-motion';
import { Mic, MicOff, Paperclip, Send, Terminal } from 'lucide-react';
import React, { useEffect, useRef, useState } from 'react';
import { useGamificationStore } from '../../stores/gamificationStore';
import { usePhoenixHydraStore } from '../../stores/phoenixHydraStore';
import CommandSuggestions from './CommandSuggestions';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';

const ChatInterface: React.FC = () => {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [showCommands, setShowCommands] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Store hooks
  const { 
    messages, 
    isTyping, 
    connectionStatus, 
    sendMessage, 
    executeCommand 
  } = usePhoenixHydraStore();
  
  const { addXP } = useGamificationStore();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Handle message submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    const trimmedMessage = message.trim();
    
    // Check if it's a command (starts with /)
    if (trimmedMessage.startsWith('/')) {
      executeCommand(trimmedMessage);
      addXP(10, 'Command executed');
    } else {
      sendMessage(trimmedMessage);
      addXP(5, 'Message sent');
    }
    
    setMessage('');
    setShowCommands(false);
  };

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    } else if (e.key === '/' && message === '') {
      setShowCommands(true);
    } else if (e.key === 'Escape') {
      setShowCommands(false);
    }
  };

  // Handle voice recording (placeholder for now)
  const toggleRecording = () => {
    setIsRecording(!isRecording);
    // TODO: Implement actual voice recording
    if (!isRecording) {
      console.log('Started voice recording...');
    } else {
      console.log('Stopped voice recording...');
    }
  };

  // Handle file upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      sendMessage(`📎 Uploaded file: ${file.name} (${(file.size / 1024).toFixed(1)}KB)`);
      addXP(15, 'File uploaded');
    }
  };

  // Handle command selection
  const handleCommandSelect = (command: string) => {
    setMessage(command);
    setShowCommands(false);
    inputRef.current?.focus();
  };

  // Phoenix Hydra specific commands
  const phoenixCommands = [
    { command: '/status', description: 'Check Phoenix Hydra system status' },
    { command: '/containers', description: 'List all containers' },
    { command: '/logs', description: 'View system logs' },
    { command: '/deploy', description: 'Deploy Phoenix Hydra services' },
    { command: '/restart', description: 'Restart a specific service' },
    { command: '/metrics', description: 'Show system metrics' },
    { command: '/health', description: 'Health check all services' },
    { command: '/backup', description: 'Create system backup' }
  ];

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Chat Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between p-4 border-b border-border/50 glass-dark"
      >
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center">
            <span className="text-white font-bold">AI</span>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">Phoenix Hydra Assistant</h2>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                connectionStatus === 'connected' 
                  ? 'bg-success animate-pulse' 
                  : connectionStatus === 'connecting'
                  ? 'bg-warning animate-pulse'
                  : 'bg-error'
              }`} />
              <span className="text-xs text-muted-foreground capitalize">
                {connectionStatus === 'connected' ? 'Local Phoenix Hydra Connected' : connectionStatus}
              </span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowCommands(!showCommands)}
            className={`p-2 rounded-lg transition-colors duration-200 ${
              showCommands 
                ? 'bg-primary text-primary-foreground' 
                : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
            }`}
            title="Show Commands"
          >
            <Terminal size={18} />
          </button>
        </div>
      </motion.div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">
        <AnimatePresence>
          {messages.map((msg, index) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              isLast={index === messages.length - 1}
            />
          ))}
        </AnimatePresence>
        
        {/* Typing Indicator */}
        {isTyping && <TypingIndicator />}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Command Suggestions */}
      <AnimatePresence>
        {showCommands && (
          <CommandSuggestions
            commands={phoenixCommands}
            onSelect={handleCommandSelect}
            onClose={() => setShowCommands(false)}
          />
        )}
      </AnimatePresence>

      {/* Input Area */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-4 border-t border-border/50 glass-dark"
      >
        <form onSubmit={handleSubmit} className="flex items-end space-x-3">
          {/* File Upload */}
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileUpload}
            className="hidden"
            accept=".txt,.json,.yaml,.yml,.py,.js,.ts,.md"
          />
          
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="p-3 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors duration-200"
            title="Upload File"
          >
            <Paperclip size={20} />
          </button>

          {/* Message Input */}
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder={
                connectionStatus === 'connected' 
                  ? "Ask Phoenix Hydra anything... (type / for commands)"
                  : "Connecting to local Phoenix Hydra..."
              }
              disabled={connectionStatus !== 'connected'}
              className="w-full p-3 pr-12 bg-muted border border-border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary text-foreground placeholder-muted-foreground disabled:opacity-50 disabled:cursor-not-allowed"
              rows={message.split('\n').length}
              style={{ minHeight: '52px', maxHeight: '120px' }}
            />
            
            {/* Character Count */}
            {message.length > 0 && (
              <div className="absolute bottom-2 right-2 text-xs text-muted-foreground">
                {message.length}
              </div>
            )}
          </div>

          {/* Voice Recording */}
          <button
            type="button"
            onClick={toggleRecording}
            className={`p-3 rounded-lg transition-all duration-200 ${
              isRecording
                ? 'bg-error text-error-foreground animate-pulse'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
            }`}
            title={isRecording ? 'Stop Recording' : 'Start Voice Recording'}
          >
            {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
          </button>

          {/* Send Button */}
          <motion.button
            type="submit"
            disabled={!message.trim() || connectionStatus !== 'connected'}
            className="p-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            title="Send Message"
          >
            <Send size={20} />
          </motion.button>
        </form>

        {/* Quick Actions */}
        <div className="flex items-center justify-between mt-3 text-xs text-muted-foreground">
          <div className="flex items-center space-x-4">
            <span>💡 Tip: Use / for Phoenix Hydra commands</span>
            <span>🎯 Local deployment at localhost:8080</span>
          </div>
          <div className="flex items-center space-x-2">
            <span>Press</span>
            <kbd className="px-2 py-1 bg-muted rounded text-xs">Enter</kbd>
            <span>to send</span>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default ChatInterface;