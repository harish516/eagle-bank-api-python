"""Event-driven architecture implementation."""

from typing import Dict, Any, Callable, List
from abc import ABC, abstractmethod
import asyncio
import json
import structlog
import redis.asyncio as aioredis
from datetime import datetime
import uuid

from .config import settings


logger = structlog.get_logger(__name__)


class Event:
    """Domain event base class."""
    
    def __init__(self, event_type: str, data: Dict[str, Any], 
                 event_id: str = None, timestamp: datetime = None):
        self.event_id = event_id or str(uuid.uuid4())
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


class EventHandler(ABC):
    """Abstract event handler."""
    
    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Handle the event."""
        pass


class EventBus:
    """Redis-based event bus implementation."""
    
    def __init__(self):
        self.redis: aioredis.Redis = None
        self.handlers: Dict[str, List[EventHandler]] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self._running = False
    
    async def initialize(self) -> None:
        """Initialize the event bus."""
        self.redis = aioredis.from_url(settings.event_bus_url)
        await self.redis.ping()
        logger.info("Event bus initialized")
    
    async def close(self) -> None:
        """Close the event bus."""
        self._running = False
        if self.redis:
            await self.redis.close()
        logger.info("Event bus closed")
    
    async def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event."""
        event = Event(event_type, data)
        
        try:
            # Publish to Redis channel
            await self.redis.publish(
                f"events:{event_type}",
                json.dumps(event.to_dict())
            )
            
            # Call local handlers
            await self._handle_local_event(event)
            
            logger.info(
                "Event published",
                event_type=event_type,
                event_id=event.event_id
            )
        
        except Exception as e:
            logger.error(
                "Failed to publish event",
                event_type=event_type,
                error=str(e),
                exc_info=e
            )
            raise
    
    async def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(handler)
        
        logger.info(
            "Subscribed to event",
            event_type=event_type,
            handler=handler.__name__
        )
    
    async def register_handler(self, event_type: str, handler: EventHandler) -> None:
        """Register an event handler."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        
        logger.info(
            "Event handler registered",
            event_type=event_type,
            handler=handler.__class__.__name__
        )
    
    async def start_listening(self) -> None:
        """Start listening for events from Redis."""
        if not self.redis:
            raise RuntimeError("Event bus not initialized")
        
        self._running = True
        
        try:
            pubsub = self.redis.pubsub()
            await pubsub.psubscribe("events:*")
            
            logger.info("Started listening for events")
            
            async for message in pubsub.listen():
                if not self._running:
                    break
                
                if message["type"] == "pmessage":
                    await self._handle_redis_message(message)
        
        except Exception as e:
            logger.error("Error in event listener", exc_info=e)
        
        finally:
            await pubsub.unsubscribe()
            logger.info("Stopped listening for events")
    
    async def _handle_redis_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming Redis message."""
        try:
            # Parse event data
            event_data = json.loads(message["data"])
            event = Event.from_dict(event_data)
            
            # Handle the event
            await self._handle_local_event(event)
            
        except Exception as e:
            logger.error("Failed to handle Redis message", exc_info=e)
    
    async def _handle_local_event(self, event: Event) -> None:
        """Handle event with local handlers and subscribers."""
        # Call registered handlers
        if event.event_type in self.handlers:
            for handler in self.handlers[event.event_type]:
                try:
                    await handler.handle(event)
                except Exception as e:
                    logger.error(
                        "Event handler failed",
                        event_type=event.event_type,
                        handler=handler.__class__.__name__,
                        exc_info=e
                    )
        
        # Call subscribers
        if event.event_type in self.subscribers:
            for subscriber in self.subscribers[event.event_type]:
                try:
                    if asyncio.iscoroutinefunction(subscriber):
                        await subscriber(event)
                    else:
                        subscriber(event)
                except Exception as e:
                    logger.error(
                        "Event subscriber failed",
                        event_type=event.event_type,
                        subscriber=subscriber.__name__,
                        exc_info=e
                    )


# Domain Events

class AccountCreatedEvent(Event):
    """Event fired when an account is created."""
    
    def __init__(self, account_data: Dict[str, Any]):
        super().__init__("account.created", account_data)


class TransactionCreatedEvent(Event):
    """Event fired when a transaction is created."""
    
    def __init__(self, transaction_data: Dict[str, Any]):
        super().__init__("transaction.created", transaction_data)


class UserCreatedEvent(Event):
    """Event fired when a user is created."""
    
    def __init__(self, user_data: Dict[str, Any]):
        super().__init__("user.created", user_data)


class BalanceUpdatedEvent(Event):
    """Event fired when account balance is updated."""
    
    def __init__(self, account_number: str, old_balance: float, new_balance: float):
        super().__init__(
            "account.balance_updated",
            {
                "account_number": account_number,
                "old_balance": old_balance,
                "new_balance": new_balance
            }
        )
