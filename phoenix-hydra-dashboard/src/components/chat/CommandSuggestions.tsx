import { motion } from 'framer-motion';
import { Terminal, X } from 'lucide-react';
import React from 'react';

interface Command {
  command: string;
  description: string;
}

interface CommandSuggestionsProps {
  commands: Command[];
  onSelect: (command: string) => void;
  onClose: () => void;
}

const CommandSuggestions: React.FC<CommandSuggestionsProps> = ({
  commands,
  onSelect,
  onClose
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 20, scale: 0.95 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="mx-4 mb-4 glass-dark border border-border/50 rounded-lg overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-border/50">
        <div className="flex items-center space-x-2">
          <Terminal size={16} className="text-primary" />
          <span className="text-sm font-medium text-foreground">
            Phoenix Hydra Commands
          </span>
        </div>
        <button
          onClick={onClose}
          className="text-muted-foreground hover:text-foreground transition-colors duration-200"
        >
          <X size={16} />
        </button>
      </div>

      {/* Commands List */}
      <div className="max-h-64 overflow-y-auto custom-scrollbar">
        {commands.map((cmd, index) => (
          <motion.button
            key={cmd.command}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2, delay: index * 0.05 }}
            onClick={() => onSelect(cmd.command)}
            className="w-full p-3 text-left hover:bg-muted/50 transition-colors duration-200 border-b border-border/20 last:border-b-0"
          >
            <div className="flex items-start space-x-3">
              <code className="text-primary font-mono text-sm bg-primary/10 px-2 py-1 rounded">
                {cmd.command}
              </code>
              <div className="flex-1">
                <p className="text-sm text-foreground">{cmd.description}</p>
              </div>
            </div>
          </motion.button>
        ))}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-border/50 bg-muted/20">
        <p className="text-xs text-muted-foreground">
          💡 Tip: These commands interact directly with your local Phoenix Hydra system
        </p>
      </div>
    </motion.div>
  );
};

export default CommandSuggestions;