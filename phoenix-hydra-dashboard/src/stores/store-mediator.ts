import { useGamificationStore } from './gamificationStore';
import { usePhoenixHydraStore } from './phoenixHydraStore';

export function setupStoreMediator() {
  usePhoenixHydraStore.subscribe(
    (state) => state.messages,
    (messages) => {
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
    }
  );
}
