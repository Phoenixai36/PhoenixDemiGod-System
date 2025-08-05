"""
Phoenix Hydra Chatbot Agent

Main chatbot agent that handles user interactions and system communication.
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from src.event_routing import Event, EventPattern, EventRouter, Subscription

from .animation_controller import AnimationController
from .gamification_system import GamificationSystem
from .personality_engine import PersonalityEngine


@dataclass
class ChatMessage:
    """Represents a chat message between user and bot"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    message_type: str = "user"  # user, bot, system
    context: Dict[str, Any] = field(default_factory=dict)
    animation_trigger: Optional[str] = None
    gamification_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserSession:
    """Tracks user session data and progress"""
    user_id: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    messages: List[ChatMessage] = field(default_factory=list)
    user_level: int = 1
    experience_points: int = 0
    achievements: List[str] = field(default_factory=list)
    personality_state: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)


class ChatbotAgent:
    """
    Main chatbot agent for Phoenix Hydra system.
    
    Provides a gamified interface between users and the Phoenix Hydra system,
    with personality-driven responses and animated interactions.
    """
    
    def __init__(self, event_router: EventRouter):
        """Initialize the chatbot agent"""
        self.event_router = event_router
        self.personality_engine = PersonalityEngine()
        self.gamification_system = GamificationSystem()
        self.animation_controller = AnimationController()
        
        # Session management
        self.active_sessions: Dict[str, UserSession] = {}
        self.message_handlers: Dict[str, Callable] = {}
        
        # System integration
        self.system_commands = {
            "/status": self._handle_system_status,
            "/deploy": self._handle_deployment,
            "/logs": self._handle_logs,
            "/metrics": self._handle_metrics,
            "/help": self._handle_help,
            "/profile": self._handle_user_profile,
            "/achievements": self._handle_achievements,
            "/leaderboard": self._handle_leaderboard,
        }
        
        # Subscribe to Phoenix Hydra events
        self._setup_event_subscriptions()
    
    def _setup_event_subscriptions(self):
        """Setup event subscriptions for system integration"""
        # Subscribe to container events
        container_pattern = EventPattern("container.*")
        container_subscription = Subscription(
            pattern=container_pattern,
            handler=self._handle_container_event,
            priority=5
        )
        self.event_router.subscribe(container_subscription)
        
        # Subscribe to deployment events
        deploy_pattern = EventPattern("deployment.*")
        deploy_subscription = Subscription(
            pattern=deploy_pattern,
            handler=self._handle_deployment_event,
            priority=5
        )
        self.event_router.subscribe(deploy_subscription)
        
        # Subscribe to error events
        error_pattern = EventPattern("error.*")
        error_subscription = Subscription(
            pattern=error_pattern,
            handler=self._handle_error_event,
            priority=10
        )
        self.event_router.subscribe(error_subscription)
    
    async def start_chat_session(self, user_id: str) -> UserSession:
        """Start a new chat session for a user"""
        session = UserSession(user_id=user_id)
        self.active_sessions[user_id] = session
        
        # Send welcome message with personality
        welcome_msg = await self.personality_engine.generate_welcome_message(session)
        welcome_chat_msg = ChatMessage(
            user_id=user_id,
            message=welcome_msg["message"],
            message_type="bot",
            animation_trigger=welcome_msg.get("animation", "wave"),
            gamification_data={"xp_gained": 10, "reason": "session_start"}
        )
        
        session.messages.append(welcome_chat_msg)
        
        # Award welcome XP
        await self.gamification_system.award_experience(session, 10, "Welcome to Phoenix Hydra!")
        
        # Publish session start event
        session_event = Event.create(
            event_type="chatbot.session.started",
            source="chatbot_agent",
            payload={
                "user_id": user_id,
                "session_id": session.session_id,
                "timestamp": session.start_time.isoformat()
            }
        )
        await self.event_router.publish(session_event)
        
        return session
    
    async def process_message(self, user_id: str, message: str) -> ChatMessage:
        """Process a user message and generate response"""
        session = self.active_sessions.get(user_id)
        if not session:
            session = await self.start_chat_session(user_id)
        
        # Update session activity
        session.last_activity = datetime.now()
        
        # Create user message
        user_msg = ChatMessage(
            user_id=user_id,
            message=message,
            message_type="user"
        )
        session.messages.append(user_msg)
        
        # Check for system commands
        if message.startswith("/"):
            return await self._handle_system_command(session, message)
        
        # Generate personality-driven response
        response_data = await self.personality_engine.generate_response(
            session, message
        )
        
        # Create bot response
        bot_msg = ChatMessage(
            user_id=user_id,
            message=response_data["message"],
            message_type="bot",
            animation_trigger=response_data.get("animation"),
            gamification_data=response_data.get("gamification", {})
        )
        session.messages.append(bot_msg)
        
        # Award XP for interaction
        xp_gained = response_data.get("gamification", {}).get("xp", 5)
        if xp_gained > 0:
            await self.gamification_system.award_experience(
                session, xp_gained, "Chat interaction"
            )
        
        # Publish chat event
        chat_event = Event.create(
            event_type="chatbot.message.processed",
            source="chatbot_agent",
            payload={
                "user_id": user_id,
                "session_id": session.session_id,
                "message_length": len(message),
                "response_type": response_data.get("type", "general")
            }
        )
        await self.event_router.publish(chat_event)
        
        return bot_msg
    
    async def _handle_system_command(self, session: UserSession, command: str) -> ChatMessage:
        """Handle system commands"""
        cmd_parts = command.split()
        cmd_name = cmd_parts[0]
        cmd_args = cmd_parts[1:] if len(cmd_parts) > 1 else []
        
        if cmd_name in self.system_commands:
            try:
                response = await self.system_commands[cmd_name](session, cmd_args)
                
                # Award XP for using system commands
                await self.gamification_system.award_experience(
                    session, 15, f"Used system command: {cmd_name}"
                )
                
                return ChatMessage(
                    user_id=session.user_id,
                    message=response["message"],
                    message_type="system",
                    animation_trigger=response.get("animation", "terminal"),
                    gamification_data={"xp_gained": 15, "reason": "system_command"}
                )
            except Exception as e:
                return ChatMessage(
                    user_id=session.user_id,
                    message=f"🚨 Command failed: {str(e)}",
                    message_type="system",
                    animation_trigger="error"
                )
        else:
            return ChatMessage(
                user_id=session.user_id,
                message=f"🤔 Unknown command: {cmd_name}. Type /help for available commands.",
                message_type="system",
                animation_trigger="confused"
            )
    
    async def _handle_system_status(self, session: UserSession, args: List[str]) -> Dict[str, Any]:
        """Handle /status command"""
        # Get system status from Phoenix Hydra
        status_event = Event.create(
            event_type="system.status.request",
            source="chatbot_agent",
            payload={"requested_by": session.user_id}
        )
        await self.event_router.publish(status_event)
        
        # Mock status for now - in real implementation, wait for response event
        status_msg = """🚀 **Phoenix Hydra System Status**

🟢 **Core Services**: All systems operational
🟢 **Event Router**: Processing events normally  
🟢 **Database**: Connected and healthy
🟢 **Containers**: 5/5 running smoothly

📊 **Performance**:
- CPU Usage: 23%
- Memory: 1.2GB / 4GB
- Active Sessions: 3
- Events Processed: 1,247 today

🎮 **Your Stats**: Level {level} | {xp} XP""".format(
            level=session.user_level,
            xp=session.experience_points
        )
        
        return {
            "message": status_msg,
            "animation": "dashboard",
            "type": "system_status"
        }
    
    async def _handle_deployment(self, session: UserSession, args: List[str]) -> Dict[str, Any]:
        """Handle /deploy command"""
        if not args:
            return {
                "message": "🚀 **Deployment Options**:\n\n"
                          "• `/deploy status` - Check deployment status\n"
                          "• `/deploy start` - Start deployment process\n"
                          "• `/deploy logs` - View deployment logs\n"
                          "• `/deploy rollback` - Rollback to previous version",
                "animation": "rocket"
            }
        
        action = args[0].lower()
        
        if action == "start":
            # Trigger deployment
            deploy_event = Event.create(
                event_type="deployment.start.request",
                source="chatbot_agent",
                payload={
                    "requested_by": session.user_id,
                    "deployment_type": "manual"
                }
            )
            await self.event_router.publish(deploy_event)
            
            return {
                "message": "🚀 **Deployment Started!**\n\n"
                          "Initiating Phoenix Hydra deployment sequence...\n"
                          "This might take a few minutes. I'll keep you updated! 🤖",
                "animation": "deploy",
                "type": "deployment_start"
            }
        
        elif action == "status":
            return {
                "message": "📊 **Deployment Status**: Ready for deployment\n"
                          "Last deployment: 2 hours ago ✅\n"
                          "Next scheduled: Not scheduled",
                "animation": "status_check"
            }
        
        return {"message": f"Unknown deployment action: {action}", "animation": "confused"}
    
    async def _handle_logs(self, session: UserSession, args: List[str]) -> Dict[str, Any]:
        """Handle /logs command"""
        service = args[0] if args else "all"
        
        # Mock logs - in real implementation, fetch from logging system
        logs_msg = f"""📋 **Recent Logs ({service})**:

```
[2025-02-08 13:45:23] INFO: Event router processing 15 events/sec
[2025-02-08 13:45:20] INFO: Container health check passed
[2025-02-08 13:45:18] DEBUG: User {session.user_id} gained 15 XP
[2025-02-08 13:45:15] INFO: Database connection stable
[2025-02-08 13:45:10] WARN: High memory usage detected (85%)
```

💡 Use `/logs <service>` to filter by specific service."""
        
        return {
            "message": logs_msg,
            "animation": "terminal",
            "type": "logs"
        }
    
    async def _handle_metrics(self, session: UserSession, args: List[str]) -> Dict[str, Any]:
        """Handle /metrics command"""
        metrics_msg = """📈 **Phoenix Hydra Metrics**

🔥 **Performance**:
- Events/sec: 15.3 avg
- Response time: 45ms avg
- Uptime: 99.8%

🎮 **Gamification**:
- Active users: 12
- Total XP awarded today: 2,847
- Achievements unlocked: 23

🏆 **Top Performers**:
1. TechWizard_42 - Level 15 (2,340 XP)
2. CodeNinja_99 - Level 12 (1,890 XP)  
3. You - Level {level} ({xp} XP)""".format(
            level=session.user_level,
            xp=session.experience_points
        )
        
        return {
            "message": metrics_msg,
            "animation": "charts",
            "type": "metrics"
        }
    
    async def _handle_help(self, session: UserSession, args: List[str]) -> Dict[str, Any]:
        """Handle /help command"""
        help_msg = """🤖 **Phoenix Hydra Chatbot Commands**

🔧 **System Commands**:
• `/status` - System health and status
• `/deploy` - Deployment management  
• `/logs [service]` - View system logs
• `/metrics` - Performance metrics

🎮 **Gamification**:
• `/profile` - Your user profile
• `/achievements` - Your achievements
• `/leaderboard` - Top users

💬 **Chat Features**:
• Ask me about Phoenix Hydra
• Get help with deployments
• Monitor system health
• Earn XP and unlock achievements!

🎨 **Animations**: I respond with different animations based on context!"""
        
        return {
            "message": help_msg,
            "animation": "help",
            "type": "help"
        }
    
    async def _handle_user_profile(self, session: UserSession, args: List[str]) -> Dict[str, Any]:
        """Handle /profile command"""
        profile_msg = f"""👤 **Your Phoenix Hydra Profile**

🎮 **Stats**:
- Level: {session.user_level}
- Experience: {session.experience_points} XP
- Next Level: {(session.user_level * 100) - session.experience_points} XP needed

🏆 **Achievements**: {len(session.achievements)} unlocked
{chr(10).join(f"• {achievement}" for achievement in session.achievements[-5:])}

📊 **Session**:
- Messages sent: {len([m for m in session.messages if m.message_type == 'user'])}
- Commands used: {len([m for m in session.messages if m.message.startswith('/')])}
- Session time: {(datetime.now() - session.start_time).seconds // 60} minutes"""
        
        return {
            "message": profile_msg,
            "animation": "profile",
            "type": "profile"
        }
    
    async def _handle_achievements(self, session: UserSession, args: List[str]) -> Dict[str, Any]:
        """Handle /achievements command"""
        all_achievements = await self.gamification_system.get_available_achievements()
        user_achievements = set(session.achievements)
        
        unlocked = [a for a in all_achievements if a["id"] in user_achievements]
        locked = [a for a in all_achievements if a["id"] not in user_achievements]
        
        achievements_msg = f"""🏆 **Achievements ({len(unlocked)}/{len(all_achievements)})**

✅ **Unlocked**:
{chr(10).join(f"• {a['name']} - {a['description']}" for a in unlocked[:5])}

🔒 **Locked**:
{chr(10).join(f"• {a['name']} - {a['description']}" for a in locked[:3])}

Keep chatting and using commands to unlock more! 🎮"""
        
        return {
            "message": achievements_msg,
            "animation": "trophy",
            "type": "achievements"
        }
    
    async def _handle_leaderboard(self, session: UserSession, args: List[str]) -> Dict[str, Any]:
        """Handle /leaderboard command"""
        # Mock leaderboard - in real implementation, fetch from database
        leaderboard_msg = """🏆 **Phoenix Hydra Leaderboard**

👑 **Top Users This Week**:
1. 🥇 TechWizard_42 - Level 15 (2,340 XP)
2. 🥈 CodeNinja_99 - Level 12 (1,890 XP)
3. 🥉 SystemMaster - Level 11 (1,650 XP)
4. 🏅 DevOpsGuru - Level 10 (1,420 XP)
5. 🏅 CloudHacker - Level 9 (1,200 XP)

📊 **Your Rank**: #12 (Level {level}, {xp} XP)

🎯 **Weekly Challenge**: Deploy 5 services
Progress: 2/5 deployments""".format(
            level=session.user_level,
            xp=session.experience_points
        )
        
        return {
            "message": leaderboard_msg,
            "animation": "leaderboard",
            "type": "leaderboard"
        }
    
    async def _handle_container_event(self, event: Event):
        """Handle container-related events"""
        # Notify active users about container events
        for session in self.active_sessions.values():
            if event.type == "container.health.unhealthy":
                notification = ChatMessage(
                    user_id=session.user_id,
                    message=f"🚨 **Alert**: Container {event.payload.get('container_name', 'unknown')} is unhealthy!",
                    message_type="system",
                    animation_trigger="alert"
                )
                session.messages.append(notification)
            elif event.type == "container.started":
                notification = ChatMessage(
                    user_id=session.user_id,
                    message=f"✅ **Info**: Container {event.payload.get('container_name', 'unknown')} started successfully!",
                    message_type="system",
                    animation_trigger="success"
                )
                session.messages.append(notification)
    
    async def _handle_deployment_event(self, event: Event):
        """Handle deployment-related events"""
        for session in self.active_sessions.values():
            if event.type == "deployment.completed":
                # Award XP for successful deployment
                await self.gamification_system.award_experience(
                    session, 50, "Deployment completed successfully!"
                )
                
                notification = ChatMessage(
                    user_id=session.user_id,
                    message="🎉 **Deployment Complete!** All services are running smoothly. +50 XP!",
                    message_type="system",
                    animation_trigger="celebration",
                    gamification_data={"xp_gained": 50, "reason": "deployment_success"}
                )
                session.messages.append(notification)
            elif event.type == "deployment.failed":
                notification = ChatMessage(
                    user_id=session.user_id,
                    message=f"❌ **Deployment Failed**: {event.payload.get('error', 'Unknown error')}",
                    message_type="system",
                    animation_trigger="error"
                )
                session.messages.append(notification)
    
    async def _handle_error_event(self, event: Event):
        """Handle error events"""
        for session in self.active_sessions.values():
            error_msg = event.payload.get('message', 'Unknown error occurred')
            notification = ChatMessage(
                user_id=session.user_id,
                message=f"⚠️ **System Error**: {error_msg}",
                message_type="system",
                animation_trigger="warning"
            )
            session.messages.append(notification)
    
    def get_session(self, user_id: str) -> Optional[UserSession]:
        """Get user session"""
        return self.active_sessions.get(user_id)
    
    def get_active_sessions(self) -> List[UserSession]:
        """Get all active sessions"""
        return list(self.active_sessions.values())
    
    async def cleanup_inactive_sessions(self, max_idle_minutes: int = 30):
        """Clean up inactive sessions"""
        current_time = datetime.now()
        inactive_sessions = []
        
        for user_id, session in self.active_sessions.items():
            idle_time = (current_time - session.last_activity).total_seconds() / 60
            if idle_time > max_idle_minutes:
                inactive_sessions.append(user_id)
        
        for user_id in inactive_sessions:
            del self.active_sessions[user_id]
            
            # Publish session end event
            session_event = Event.create(
                event_type="chatbot.session.ended",
                source="chatbot_agent",
                payload={
                    "user_id": user_id,
                    "reason": "inactivity",
                    "idle_minutes": max_idle_minutes
                }
            )
            await self.event_router.publish(session_event)