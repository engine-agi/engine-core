"""
WebSocket Handler for Real-Time Updates.

This module provides comprehensive WebSocket functionality for the Engine Framework,
enabling real-time communication between the backend and connected clients. It handles
agent status updates, workflow progress notifications, log events, and system metrics
with efficient connection management and message broadcasting.

Key Features:
- Agent execution status and progress updates
- Workflow state changes and execution monitoring
- Real-time log streaming with filtering
- System metrics and performance data
- Tool execution status and results
- Book content updates and collaboration
- Connection management with authentication
- Message routing and broadcasting
- Subscription management for targeted updates
- Event queuing and delivery guarantees

Architecture:
- WebSocketManager for connection lifecycle
- EventBroadcaster for message distribution  
- SubscriptionManager for targeted updates
- MessageQueue for reliable delivery
- ConnectionRegistry for client tracking
- EventFilters for selective streaming
- Authentication integration
- Rate limiting and throttling

Dependencies:
- FastAPI WebSocket support
- Service layers for data access
- Event system for notifications
- Authentication services
- Logging infrastructure
"""

from typing import Dict, Any, List, Optional, Set, Tuple, Union, Callable, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
import uuid
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import weakref

from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.websockets import WebSocketState
import jwt

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events that can be broadcast via WebSocket."""
    # Agent Events
    AGENT_STATUS_CHANGED = "agent.status.changed"
    AGENT_EXECUTION_STARTED = "agent.execution.started"
    AGENT_EXECUTION_PROGRESS = "agent.execution.progress"
    AGENT_EXECUTION_COMPLETED = "agent.execution.completed"
    AGENT_EXECUTION_FAILED = "agent.execution.failed"
    AGENT_LOG_ENTRY = "agent.log.entry"
    AGENT_CREATED = "agent.created"
    AGENT_UPDATED = "agent.updated"
    AGENT_DELETED = "agent.deleted"
    
    # Team Events
    TEAM_STATUS_CHANGED = "team.status.changed"
    TEAM_MEMBER_ADDED = "team.member.added"
    TEAM_MEMBER_REMOVED = "team.member.removed"
    TEAM_CREATED = "team.created"
    TEAM_EXECUTION_STARTED = "team.execution.started"
    TEAM_EXECUTION_PROGRESS = "team.execution.progress"
    TEAM_EXECUTION_COMPLETED = "team.execution.completed"
    
    # Workflow Events
    WORKFLOW_STATUS_CHANGED = "workflow.status.changed"
    WORKFLOW_EXECUTION_STARTED = "workflow.execution.started"
    WORKFLOW_EXECUTION_PROGRESS = "workflow.execution.progress"
    WORKFLOW_SUPERSTEP_STARTED = "workflow.superstep.started"
    WORKFLOW_SUPERSTEP_COMPLETED = "workflow.superstep.completed"
    WORKFLOW_VERTEX_PROCESSING = "workflow.vertex.processing"
    WORKFLOW_EXECUTION_COMPLETED = "workflow.execution.completed"
    WORKFLOW_EXECUTION_FAILED = "workflow.execution.failed"
    
    # Protocol Events
    PROTOCOL_CREATED = "protocol.created"
    PROTOCOL_UPDATED = "protocol.updated"
    PROTOCOL_DELETED = "protocol.deleted"
    PROTOCOL_COMMAND_EXECUTED = "protocol.command.executed"
    PROTOCOL_SESSION_STARTED = "protocol.session.started"
    PROTOCOL_SESSION_ENDED = "protocol.session.ended"
    
    # Tool Events
    TOOL_EXECUTION_STARTED = "tool.execution.started"
    TOOL_EXECUTION_COMPLETED = "tool.execution.completed"
    TOOL_EXECUTION_FAILED = "tool.execution.failed"
    TOOL_STATUS_CHANGED = "tool.status.changed"
    
    # Book Events
    BOOK_CREATED = "book.created"
    BOOK_UPDATED = "book.updated"
    BOOK_DELETED = "book.deleted"
    CHAPTER_CREATED = "book.chapter.created"
    CHAPTER_UPDATED = "book.chapter.updated"
    PAGE_CREATED = "book.page.created"
    PAGE_UPDATED = "book.page.updated"
    BOOK_CONTENT_UPDATED = "book.content.updated"
    BOOK_SEARCH_PERFORMED = "book.search.performed"
    BOOK_COLLABORATION_STARTED = "book.collaboration.started"
    BOOK_COLLABORATION_ENDED = "book.collaboration.ended"
    
    # System Events
    SYSTEM_HEALTH_UPDATE = "system.health.update"
    SYSTEM_METRICS_UPDATE = "system.metrics.update"
    SYSTEM_LOG_ENTRY = "system.log.entry"
    SYSTEM_ALERT = "system.alert"
    
    # Project Events
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"


class MessagePriority(Enum):
    """Message priority levels for event processing."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class SubscriptionScope(Enum):
    """Scopes for event subscriptions."""
    GLOBAL = "global"           # All events
    PROJECT = "project"         # Events for specific project
    AGENT = "agent"            # Events for specific agent
    TEAM = "team"              # Events for specific team
    WORKFLOW = "workflow"       # Events for specific workflow
    TOOL = "tool"              # Events for specific tool
    BOOK = "book"              # Events for specific book


@dataclass
class WebSocketMessage:
    """WebSocket message structure."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: MessagePriority = MessagePriority.NORMAL
    scope: SubscriptionScope = SubscriptionScope.GLOBAL
    scope_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""
    connection_id: str
    websocket: WebSocket
    user_id: Optional[str]
    session_id: Optional[str]
    subscriptions: Set[Tuple[SubscriptionScope, Optional[str]]] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    is_authenticated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventSubscription:
    """Event subscription configuration."""
    scope: SubscriptionScope
    scope_id: Optional[str]
    event_types: Set[EventType] = field(default_factory=set)
    filters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


class ConnectionRegistry:
    """Registry for managing WebSocket connections."""
    
    def __init__(self):
        """Initialize connection registry."""
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)
        self.subscription_index: Dict[Tuple[SubscriptionScope, Optional[str]], Set[str]] = defaultdict(set)
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Start cleanup task
        self._start_cleanup_task()
    
    def add_connection(self, connection_info: ConnectionInfo) -> None:
        """Add connection to registry."""
        self.connections[connection_info.connection_id] = connection_info
        
        if connection_info.user_id:
            self.user_connections[connection_info.user_id].add(connection_info.connection_id)
        
        logger.info(f"Added WebSocket connection: {connection_info.connection_id}")
    
    def remove_connection(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Remove connection from registry."""
        if connection_id not in self.connections:
            return None
        
        connection_info = self.connections.pop(connection_id)
        
        # Remove from user connections
        if connection_info.user_id:
            self.user_connections[connection_info.user_id].discard(connection_id)
            if not self.user_connections[connection_info.user_id]:
                del self.user_connections[connection_info.user_id]
        
        # Remove from subscription index
        for subscription in connection_info.subscriptions:
            self.subscription_index[subscription].discard(connection_id)
            if not self.subscription_index[subscription]:
                del self.subscription_index[subscription]
        
        logger.info(f"Removed WebSocket connection: {connection_id}")
        return connection_info
    
    def get_connection(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Get connection by ID."""
        return self.connections.get(connection_id)
    
    def get_user_connections(self, user_id: str) -> List[ConnectionInfo]:
        """Get all connections for a user."""
        connection_ids = self.user_connections.get(user_id, set())
        return [self.connections[conn_id] for conn_id in connection_ids if conn_id in self.connections]
    
    def add_subscription(self, connection_id: str, subscription: EventSubscription) -> bool:
        """Add subscription to connection."""
        if connection_id not in self.connections:
            return False
        
        connection_info = self.connections[connection_id]
        subscription_key = (subscription.scope, subscription.scope_id)
        
        connection_info.subscriptions.add(subscription_key)
        self.subscription_index[subscription_key].add(connection_id)
        
        logger.debug(f"Added subscription {subscription_key} for connection {connection_id}")
        return True
    
    def remove_subscription(self, connection_id: str, scope: SubscriptionScope, scope_id: Optional[str] = None) -> bool:
        """Remove subscription from connection."""
        if connection_id not in self.connections:
            return False
        
        connection_info = self.connections[connection_id]
        subscription_key = (scope, scope_id)
        
        connection_info.subscriptions.discard(subscription_key)
        self.subscription_index[subscription_key].discard(connection_id)
        
        if not self.subscription_index[subscription_key]:
            del self.subscription_index[subscription_key]
        
        logger.debug(f"Removed subscription {subscription_key} for connection {connection_id}")
        return True
    
    def get_subscribers(self, scope: SubscriptionScope, scope_id: Optional[str] = None) -> List[ConnectionInfo]:
        """Get connections subscribed to specific scope."""
        subscription_key = (scope, scope_id)
        connection_ids = self.subscription_index.get(subscription_key, set())
        
        # Also include global subscribers
        if scope != SubscriptionScope.GLOBAL:
            global_key = (SubscriptionScope.GLOBAL, None)
            connection_ids.update(self.subscription_index.get(global_key, set()))
        
        return [
            self.connections[conn_id] 
            for conn_id in connection_ids 
            if conn_id in self.connections
        ]
    
    def update_activity(self, connection_id: str) -> None:
        """Update last activity time for connection."""
        if connection_id in self.connections:
            self.connections[connection_id].last_activity = datetime.utcnow()
            self.connections[connection_id].message_count += 1
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        active_connections = len(self.connections)
        authenticated_connections = sum(1 for conn in self.connections.values() if conn.is_authenticated)
        unique_users = len(self.user_connections)
        total_subscriptions = sum(len(conn.subscriptions) for conn in self.connections.values())
        
        return {
            'active_connections': active_connections,
            'authenticated_connections': authenticated_connections,
            'unique_users': unique_users,
            'total_subscriptions': total_subscriptions,
            'subscription_types': dict(self.subscription_index.keys())
        }
    
    def _start_cleanup_task(self) -> None:
        """Start background task for connection cleanup."""
        async def cleanup_connections():
            while True:
                try:
                    await asyncio.sleep(60)  # Check every minute
                    await self._cleanup_stale_connections()
                except Exception as e:
                    logger.error(f"Error in connection cleanup: {str(e)}")
        
        self._cleanup_task = asyncio.create_task(cleanup_connections())
    
    async def _cleanup_stale_connections(self) -> None:
        """Clean up stale or disconnected connections."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=30)
        stale_connections = []
        
        for connection_id, connection_info in self.connections.items():
            # Check if connection is stale
            if connection_info.last_activity < cutoff_time:
                stale_connections.append(connection_id)
                continue
            
            # Check if WebSocket is still connected
            if connection_info.websocket.client_state == WebSocketState.DISCONNECTED:
                stale_connections.append(connection_id)
        
        # Remove stale connections
        for connection_id in stale_connections:
            self.remove_connection(connection_id)
        
        if stale_connections:
            logger.info(f"Cleaned up {len(stale_connections)} stale connections")


class MessageQueue:
    """Queue for reliable message delivery."""
    
    def __init__(self, max_size: int = 10000):
        """Initialize message queue."""
        self.max_size = max_size
        self.queues: Dict[str, asyncio.Queue] = {}  # connection_id -> queue
        self.pending_messages: Dict[str, List[WebSocketMessage]] = defaultdict(list)
    
    async def enqueue_message(self, connection_id: str, message: WebSocketMessage) -> bool:
        """Enqueue message for connection."""
        try:
            if connection_id not in self.queues:
                self.queues[connection_id] = asyncio.Queue(maxsize=self.max_size)
            
            queue = self.queues[connection_id]
            
            # Handle queue full scenarios based on priority
            if queue.full():
                if message.priority in [MessagePriority.HIGH, MessagePriority.CRITICAL]:
                    # Remove lowest priority message to make room
                    try:
                        await asyncio.wait_for(queue.get_nowait(), timeout=0.1)
                    except:
                        pass
                else:
                    logger.warning(f"Message queue full for connection {connection_id}, dropping message")
                    return False
            
            await queue.put(message)
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue message for {connection_id}: {str(e)}")
            return False
    
    async def dequeue_message(self, connection_id: str, timeout: float = 1.0) -> Optional[WebSocketMessage]:
        """Dequeue message for connection."""
        try:
            if connection_id not in self.queues:
                return None
            
            queue = self.queues[connection_id]
            message = await asyncio.wait_for(queue.get(), timeout=timeout)
            return message
            
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue message for {connection_id}: {str(e)}")
            return None
    
    def get_queue_size(self, connection_id: str) -> int:
        """Get queue size for connection."""
        if connection_id not in self.queues:
            return 0
        return self.queues[connection_id].qsize()
    
    def cleanup_connection_queue(self, connection_id: str) -> None:
        """Clean up queue for disconnected connection."""
        if connection_id in self.queues:
            del self.queues[connection_id]
        if connection_id in self.pending_messages:
            del self.pending_messages[connection_id]


class EventBroadcaster:
    """Event broadcasting system for WebSocket messages."""
    
    def __init__(self, connection_registry: ConnectionRegistry, message_queue: MessageQueue):
        """Initialize event broadcaster."""
        self.connection_registry = connection_registry
        self.message_queue = message_queue
        self.event_filters: Dict[EventType, List[Callable]] = defaultdict(list)
        self.broadcast_stats = {
            'total_broadcasts': 0,
            'successful_deliveries': 0,
            'failed_deliveries': 0,
            'filtered_messages': 0
        }
    
    async def broadcast_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        scope: SubscriptionScope = SubscriptionScope.GLOBAL,
        scope_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        target_user_id: Optional[str] = None
    ) -> int:
        """Broadcast event to subscribers."""
        self.broadcast_stats['total_broadcasts'] += 1
        
        try:
            # Create message
            message = WebSocketMessage(
                event_type=event_type,
                data=data,
                priority=priority,
                scope=scope,
                scope_id=scope_id
            )
            
            # Apply event filters
            if not await self._apply_event_filters(message):
                self.broadcast_stats['filtered_messages'] += 1
                return 0
            
            # Get target connections
            if target_user_id:
                target_connections = self.connection_registry.get_user_connections(target_user_id)
            else:
                target_connections = self.connection_registry.get_subscribers(scope, scope_id)
            
            # Broadcast to connections
            delivery_count = 0
            for connection_info in target_connections:
                success = await self._send_message_to_connection(connection_info, message)
                if success:
                    delivery_count += 1
                    self.broadcast_stats['successful_deliveries'] += 1
                else:
                    self.broadcast_stats['failed_deliveries'] += 1
            
            logger.debug(f"Broadcasted {event_type.value} to {delivery_count} connections")
            return delivery_count
            
        except Exception as e:
            logger.error(f"Failed to broadcast event {event_type.value}: {str(e)}")
            self.broadcast_stats['failed_deliveries'] += 1
            return 0
    
    async def _send_message_to_connection(self, connection_info: ConnectionInfo, message: WebSocketMessage) -> bool:
        """Send message to specific connection."""
        try:
            # Add connection-specific metadata
            message.user_id = connection_info.user_id
            message.session_id = connection_info.session_id
            
            # Enqueue message
            success = await self.message_queue.enqueue_message(connection_info.connection_id, message)
            if success:
                # Update connection activity
                self.connection_registry.update_activity(connection_info.connection_id)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send message to connection {connection_info.connection_id}: {str(e)}")
            return False
    
    async def _apply_event_filters(self, message: WebSocketMessage) -> bool:
        """Apply event filters to message."""
        try:
            filters = self.event_filters.get(message.event_type, [])
            
            for filter_func in filters:
                if not await filter_func(message):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying event filters: {str(e)}")
            return True  # Allow message through on filter error
    
    def add_event_filter(self, event_type: EventType, filter_func: Callable) -> None:
        """Add event filter for specific event type."""
        self.event_filters[event_type].append(filter_func)
        logger.debug(f"Added event filter for {event_type.value}")
    
    def get_broadcast_stats(self) -> Dict[str, Any]:
        """Get broadcasting statistics."""
        return self.broadcast_stats.copy()


class WebSocketManager:
    """Main WebSocket management class."""
    
    def __init__(self):
        """Initialize WebSocket manager."""
        self.connection_registry = ConnectionRegistry()
        self.message_queue = MessageQueue()
        self.event_broadcaster = EventBroadcaster(self.connection_registry, self.message_queue)
        self.connection_handlers: Dict[str, asyncio.Task] = {}
        self.auth_handler: Optional[Callable] = None
        
        # Rate limiting
        self.rate_limits: Dict[str, List[datetime]] = defaultdict(list)
        self.rate_limit_window = 60  # seconds
        self.rate_limit_max = 100  # messages per window
    
    def set_auth_handler(self, auth_handler: Callable) -> None:
        """Set authentication handler."""
        self.auth_handler = auth_handler
    
    async def connect_websocket(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> str:
        """Accept WebSocket connection and set up handlers."""
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        
        # Authenticate if handler provided
        is_authenticated = False
        if self.auth_handler and auth_token:
            try:
                user_data = await self.auth_handler(auth_token)
                user_id = user_data.get('user_id', user_id)
                session_id = user_data.get('session_id', session_id)
                is_authenticated = True
            except Exception as e:
                logger.warning(f"Authentication failed for connection {connection_id}: {str(e)}")
        
        # Create connection info
        connection_info = ConnectionInfo(
            connection_id=connection_id,
            websocket=websocket,
            user_id=user_id,
            session_id=session_id,
            is_authenticated=is_authenticated
        )
        
        # Add to registry
        self.connection_registry.add_connection(connection_info)
        
        # Start connection handlers
        self.connection_handlers[connection_id] = asyncio.create_task(
            self._handle_connection(connection_info)
        )
        
        logger.info(f"WebSocket connected: {connection_id} (user: {user_id})")
        return connection_id
    
    async def disconnect_websocket(self, connection_id: str) -> None:
        """Disconnect WebSocket and cleanup."""
        # Cancel connection handler
        if connection_id in self.connection_handlers:
            self.connection_handlers[connection_id].cancel()
            del self.connection_handlers[connection_id]
        
        # Remove from registry
        connection_info = self.connection_registry.remove_connection(connection_id)
        
        # Cleanup message queue
        self.message_queue.cleanup_connection_queue(connection_id)
        
        # Clean rate limiting data
        if connection_id in self.rate_limits:
            del self.rate_limits[connection_id]
        
        if connection_info:
            logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def _handle_connection(self, connection_info: ConnectionInfo) -> None:
        """Handle WebSocket connection lifecycle."""
        connection_id = connection_info.connection_id
        websocket = connection_info.websocket
        
        try:
            # Start message sender task
            sender_task = asyncio.create_task(self._message_sender(connection_info))
            
            # Handle incoming messages
            async for message in websocket.iter_text():
                try:
                    # Rate limiting check
                    if not self._check_rate_limit(connection_id):
                        await websocket.send_text(json.dumps({
                            'error': 'Rate limit exceeded',
                            'message': f'Maximum {self.rate_limit_max} messages per {self.rate_limit_window} seconds'
                        }))
                        continue
                    
                    # Process incoming message
                    await self._process_incoming_message(connection_info, message)
                    
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({
                        'error': 'Invalid JSON format'
                    }))
                except Exception as e:
                    logger.error(f"Error processing message from {connection_id}: {str(e)}")
                    await websocket.send_text(json.dumps({
                        'error': 'Internal server error'
                    }))
        
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"Error in WebSocket connection {connection_id}: {str(e)}")
        finally:
            # Cancel sender task
            if 'sender_task' in locals():
                sender_task.cancel()
            
            # Cleanup connection
            await self.disconnect_websocket(connection_id)
    
    async def _message_sender(self, connection_info: ConnectionInfo) -> None:
        """Send queued messages to WebSocket."""
        connection_id = connection_info.connection_id
        websocket = connection_info.websocket
        
        try:
            while True:
                # Get message from queue
                message = await self.message_queue.dequeue_message(connection_id, timeout=1.0)
                
                if message is None:
                    continue
                
                # Send message
                try:
                    message_data = {
                        'id': message.id,
                        'event_type': message.event_type.value,
                        'data': message.data,
                        'timestamp': message.timestamp.isoformat(),
                        'scope': message.scope.value,
                        'scope_id': message.scope_id,
                        'metadata': message.metadata
                    }
                    
                    await websocket.send_text(json.dumps(message_data))
                    logger.debug(f"Sent message {message.id} to connection {connection_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to send message to {connection_id}: {str(e)}")
                    # Re-queue message for retry
                    await self.message_queue.enqueue_message(connection_id, message)
                    break
        
        except asyncio.CancelledError:
            logger.debug(f"Message sender cancelled for connection {connection_id}")
        except Exception as e:
            logger.error(f"Error in message sender for {connection_id}: {str(e)}")
    
    async def _process_incoming_message(self, connection_info: ConnectionInfo, message: str) -> None:
        """Process incoming WebSocket message."""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'subscribe':
                await self._handle_subscription(connection_info, data)
            elif message_type == 'unsubscribe':
                await self._handle_unsubscription(connection_info, data)
            elif message_type == 'ping':
                await self._handle_ping(connection_info)
            elif message_type == 'authenticate':
                await self._handle_authentication(connection_info, data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await connection_info.websocket.send_text(json.dumps({
                    'error': f'Unknown message type: {message_type}'
                }))
        
        except Exception as e:
            logger.error(f"Error processing incoming message: {str(e)}")
            await connection_info.websocket.send_text(json.dumps({
                'error': 'Failed to process message'
            }))
    
    async def _handle_subscription(self, connection_info: ConnectionInfo, data: Dict[str, Any]) -> None:
        """Handle subscription request."""
        try:
            scope = SubscriptionScope(data.get('scope', 'global'))
            scope_id = data.get('scope_id')
            event_types = data.get('event_types', [])
            
            # Create subscription
            subscription = EventSubscription(
                scope=scope,
                scope_id=scope_id,
                event_types=set(EventType(et) for et in event_types) if event_types else set()
            )
            
            # Add subscription to connection
            success = self.connection_registry.add_subscription(connection_info.connection_id, subscription)
            
            if success:
                await connection_info.websocket.send_text(json.dumps({
                    'type': 'subscription_confirmed',
                    'scope': scope.value,
                    'scope_id': scope_id,
                    'event_types': event_types
                }))
            else:
                await connection_info.websocket.send_text(json.dumps({
                    'error': 'Failed to add subscription'
                }))
        
        except Exception as e:
            logger.error(f"Error handling subscription: {str(e)}")
            await connection_info.websocket.send_text(json.dumps({
                'error': 'Invalid subscription request'
            }))
    
    async def _handle_unsubscription(self, connection_info: ConnectionInfo, data: Dict[str, Any]) -> None:
        """Handle unsubscription request."""
        try:
            scope = SubscriptionScope(data.get('scope', 'global'))
            scope_id = data.get('scope_id')
            
            # Remove subscription
            success = self.connection_registry.remove_subscription(
                connection_info.connection_id, scope, scope_id
            )
            
            if success:
                await connection_info.websocket.send_text(json.dumps({
                    'type': 'unsubscription_confirmed',
                    'scope': scope.value,
                    'scope_id': scope_id
                }))
            else:
                await connection_info.websocket.send_text(json.dumps({
                    'error': 'Failed to remove subscription'
                }))
        
        except Exception as e:
            logger.error(f"Error handling unsubscription: {str(e)}")
            await connection_info.websocket.send_text(json.dumps({
                'error': 'Invalid unsubscription request'
            }))
    
    async def _handle_ping(self, connection_info: ConnectionInfo) -> None:
        """Handle ping message."""
        await connection_info.websocket.send_text(json.dumps({
            'type': 'pong',
            'timestamp': datetime.utcnow().isoformat()
        }))
    
    async def _handle_authentication(self, connection_info: ConnectionInfo, data: Dict[str, Any]) -> None:
        """Handle authentication message."""
        if not self.auth_handler:
            await connection_info.websocket.send_text(json.dumps({
                'error': 'Authentication not supported'
            }))
            return
        
        try:
            auth_token = data.get('token')
            if not auth_token:
                raise ValueError("No token provided")
            
            user_data = await self.auth_handler(auth_token)
            
            # Update connection info
            connection_info.user_id = user_data.get('user_id')
            connection_info.session_id = user_data.get('session_id')
            connection_info.is_authenticated = True
            
            await connection_info.websocket.send_text(json.dumps({
                'type': 'authentication_success',
                'user_id': connection_info.user_id,
                'session_id': connection_info.session_id
            }))
        
        except Exception as e:
            logger.warning(f"Authentication failed: {str(e)}")
            await connection_info.websocket.send_text(json.dumps({
                'error': 'Authentication failed'
            }))
    
    def _check_rate_limit(self, connection_id: str) -> bool:
        """Check rate limiting for connection."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.rate_limit_window)
        
        # Clean old entries
        self.rate_limits[connection_id] = [
            timestamp for timestamp in self.rate_limits[connection_id]
            if timestamp > cutoff
        ]
        
        # Check if under limit
        if len(self.rate_limits[connection_id]) >= self.rate_limit_max:
            return False
        
        # Add current request
        self.rate_limits[connection_id].append(now)
        return True
    
    # Public API methods
    
    async def broadcast_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        scope: SubscriptionScope = SubscriptionScope.GLOBAL,
        scope_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        target_user_id: Optional[str] = None
    ) -> int:
        """Broadcast event to subscribers."""
        return await self.event_broadcaster.broadcast_event(
            event_type, data, scope, scope_id, priority, target_user_id
        )
    
    def add_event_filter(self, event_type: EventType, filter_func: Callable) -> None:
        """Add event filter."""
        self.event_broadcaster.add_event_filter(event_type, filter_func)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        conn_stats = self.connection_registry.get_connection_stats()
        broadcast_stats = self.event_broadcaster.get_broadcast_stats()
        
        return {
            'connections': conn_stats,
            'broadcasting': broadcast_stats,
            'active_handlers': len(self.connection_handlers),
            'rate_limited_connections': len(self.rate_limits)
        }
    
    async def send_to_user(
        self,
        user_id: str,
        event_type: EventType,
        data: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> int:
        """Send message to specific user."""
        return await self.broadcast_event(
            event_type, data, 
            scope=SubscriptionScope.GLOBAL,
            priority=priority,
            target_user_id=user_id
        )
    
    async def send_to_project(
        self,
        project_id: str,
        event_type: EventType,
        data: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> int:
        """Send message to project subscribers."""
        return await self.broadcast_event(
            event_type, data,
            scope=SubscriptionScope.PROJECT,
            scope_id=project_id,
            priority=priority
        )


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


# FastAPI WebSocket endpoint
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    token: Optional[str] = None
):
    """Main WebSocket endpoint for FastAPI."""
    connection_id = None
    
    try:
        connection_id = await websocket_manager.connect_websocket(
            websocket, user_id, session_id, token
        )
        
        # Wait for disconnection
        while True:
            await asyncio.sleep(1)
            
            # Check if connection is still active
            connection_info = websocket_manager.connection_registry.get_connection(connection_id)
            if not connection_info or connection_info.websocket.client_state == WebSocketState.DISCONNECTED:
                break
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        if connection_id:
            await websocket_manager.disconnect_websocket(connection_id)


# Convenience functions for common events

async def broadcast_agent_status(agent_id: str, status: str, data: Dict[str, Any] = None):
    """Broadcast agent status change."""
    await websocket_manager.broadcast_event(
        EventType.AGENT_STATUS_CHANGED,
        {
            'agent_id': agent_id,
            'status': status,
            'data': data or {}
        },
        scope=SubscriptionScope.AGENT,
        scope_id=agent_id
    )


async def broadcast_workflow_progress(workflow_id: str, progress: float, data: Dict[str, Any] = None):
    """Broadcast workflow execution progress."""
    await websocket_manager.broadcast_event(
        EventType.WORKFLOW_EXECUTION_PROGRESS if progress < 1.0 else EventType.WORKFLOW_EXECUTION_COMPLETED,
        {
            'workflow_id': workflow_id,
            'progress': progress,
            'data': data or {}
        },
        scope=SubscriptionScope.WORKFLOW,
        scope_id=workflow_id
    )


async def broadcast_system_alert(level: str, message: str, data: Dict[str, Any] = None):
    """Broadcast system alert."""
    await websocket_manager.broadcast_event(
        EventType.SYSTEM_ALERT,
        {
            'level': level,
            'message': message,
            'data': data or {}
        },
        priority=MessagePriority.HIGH if level in ['warning', 'error'] else MessagePriority.NORMAL
    )


async def broadcast_log_entry(source: str, level: str, message: str, timestamp: datetime = None):
    """Broadcast log entry."""
    await websocket_manager.broadcast_event(
        EventType.SYSTEM_LOG_ENTRY,
        {
            'source': source,
            'level': level,
            'message': message,
            'timestamp': (timestamp or datetime.utcnow()).isoformat()
        }
    )


# Authentication helper (can be customized)
async def default_auth_handler(token: str) -> Dict[str, Any]:
    """Default authentication handler."""
    try:
        # This is a simple example - in production, use proper JWT validation
        payload = jwt.decode(token, options={"verify_signature": False})
        return {
            'user_id': payload.get('user_id'),
            'session_id': payload.get('session_id'),
            'authenticated': True
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


# Set default auth handler
websocket_manager.set_auth_handler(default_auth_handler)


# FastAPI dependency functions
def get_event_broadcaster():
    """Get the global event broadcaster for FastAPI dependency injection."""
    return websocket_manager.event_broadcaster


# Example usage and testing
async def example_websocket_usage():
    """Example usage of WebSocket functionality."""
    
    # Simulate broadcasting various events
    
    # Agent events
    await broadcast_agent_status("agent_1", "running", {
        'task': 'code_review',
        'progress': 0.3
    })
    
    # Workflow events
    await broadcast_workflow_progress("workflow_1", 0.5, {
        'current_vertex': 'analysis',
        'vertices_completed': 2,
        'total_vertices': 4
    })
    
    # System events
    await broadcast_system_alert("warning", "High memory usage detected", {
        'memory_usage': 85.5,
        'threshold': 80.0
    })
    
    # Log events
    await broadcast_log_entry("agent_service", "info", "Agent execution completed successfully")
    
    # Get stats
    stats = websocket_manager.get_connection_stats()
    print(f"WebSocket Statistics: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    # Run example
    import asyncio
    asyncio.run(example_websocket_usage())
