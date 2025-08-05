import { motion } from "framer-motion";
import { AlertCircle, Check, CheckCircle, Copy, Terminal } from "lucide-react";
import React from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/cjs/styles/prism";
import { ChatMessage } from "../../stores/phoenixHydraStore";

interface MessageBubbleProps {
  message: ChatMessage;
  isLast: boolean;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isLast }) => {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isUser = message.type === "user";
  const isSystem = message.type === "system";
  const isError = message.type === "error";

  // Detect code blocks
  const hasCodeBlock = message.content.includes("```");
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;

  const renderContent = () => {
    if (hasCodeBlock) {
      const parts = [];
      let lastIndex = 0;
      let match;

      while ((match = codeBlockRegex.exec(message.content)) !== null) {
        // Add text before code block
        if (match.index > lastIndex) {
          parts.push(
            <span key={`text-${lastIndex}`}>
              {message.content.slice(lastIndex, match.index)}
            </span>
          );
        }

        // Add code block
        const language = match[1] || "text";
        const code = match[2];
        parts.push(
          <div key={`code-${match.index}`} className="my-2 relative">
            <div className="flex items-center justify-between bg-muted/50 px-3 py-1 rounded-t-lg">
              <span className="text-xs text-muted-foreground">{language}</span>
              <button
                onClick={() => handleCopy(code)}
                className="text-muted-foreground hover:text-foreground transition-colors duration-200"
              >
                {copied ? <Check size={14} /> : <Copy size={14} />}
              </button>
            </div>
            <SyntaxHighlighter
              language={language}
              style={oneDark}
              customStyle={{
                margin: 0,
                borderTopLeftRadius: 0,
                borderTopRightRadius: 0,
                fontSize: "0.875rem",
              }}
            >
              {code}
            </SyntaxHighlighter>
          </div>
        );

        lastIndex = match.index + match[0].length;
      }

      // Add remaining text
      if (lastIndex < message.content.length) {
        parts.push(
          <span key={`text-${lastIndex}`}>
            {message.content.slice(lastIndex)}
          </span>
        );
      }

      return parts;
    }

    return message.content;
  };

  const getStatusIcon = () => {
    if (message.metadata?.status === "success") {
      return <CheckCircle size={16} className="text-success" />;
    } else if (message.metadata?.status === "error") {
      return <AlertCircle size={16} className="text-error" />;
    } else if (message.metadata?.command) {
      return <Terminal size={16} className="text-primary" />;
    }
    return null;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}
    >
      <div
        className={`max-w-[80%] ${
          isUser
            ? "chat-bubble-user"
            : isSystem
            ? "bg-muted/50 text-muted-foreground rounded-2xl"
            : isError
            ? "bg-error/10 border border-error/20 text-error-foreground rounded-2xl"
            : "chat-bubble-bot"
        } p-4 relative group`}
      >
        {/* Message Content */}
        <div className="prose prose-sm max-w-none">{renderContent()}</div>

        {/* Message Metadata */}
        <div className="flex items-center justify-between mt-2 text-xs opacity-70">
          <div className="flex items-center space-x-2">
            {getStatusIcon()}
            <span>
              {message.timestamp.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
            {message.metadata?.duration && (
              <span className="text-muted-foreground">
                ({message.metadata.duration}ms)
              </span>
            )}
          </div>

          {/* Copy button */}
          <button
            onClick={() => handleCopy(message.content)}
            className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:text-foreground"
            title="Copy message"
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
          </button>
        </div>

        {/* Command indicator */}
        {message.metadata?.command && (
          <div className="absolute -top-2 left-4 bg-primary text-primary-foreground px-2 py-1 rounded text-xs">
            Command
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default MessageBubble;
