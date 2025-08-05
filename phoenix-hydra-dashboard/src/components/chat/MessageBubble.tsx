import React from 'react';
import { motion } from 'framer-motion';
import { Copy, Check, Termeact';
import { ChatMessage } from '../../stores/phoenixHydraStore';

interface MessageBubbleProps {
ssage;
  isLast: boolean;
}

c


  const handleCopy = (text: string) => {

    setCopied(true);
    setTimeout(() => setCopied(false), 2
  };

  co';

  const isError = message.type === 'error';

  const getStatusIcon = () => {
{
      return <CheckCirc>;
    } else if (message.metadata?.status === 'error') {
      return <AlertCircle size={16} className="text-eor" />;
ommand) {
      return <Terminal size={16
    }
    return null;
  };

eturn (
    <motion.div
      initial={{ opacity: 0, y: 20, s
      animate={{ opacity: 1, y: 0, sca
      transition={{ d
      className={`flex ${isUser ? 'justify-e} mb-4`}
    >
      <div
        clas
         r
le-user'
            : isSystem
            ? 'bg-muted/50 text-muted-foregrd-2xl'
            : isError
            ? 'bg-ed-2xl'
            : 'chat-bubble-bot'
        } p-4 relative group`}
      >
        {/* Message C
        <div className="prose prose-sm max-w-none">
          <pre className="whitespace-pre-wrap font-sans text-sm">
            {me
          </pre>
        </div>

        {/* Message Metadata */}
        <div className="flex item0">
          <div className="fle-2">
            {getStatusIcon()}
            <span>
              {message.timestamp.toLoca{ 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            <
            {messagen && (
              <span className="t>
                ms)
          >
     )}
          </div>
          
/}
          <button
            onClick={() => handleCopy(message.c}
            classNaund"
            title="Copy message"
          >
            {copi/>}
          ton>
       >

        {/* Command
     nd && (
">
            Command
    

      </div>
    </motion.div>
  );
};

export default MessageBubble;