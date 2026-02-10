# Async Architecture Plan for MAGGxDND Web Interface

## Current Architecture Overview

The MAGGxDND project is a D&D game engine with a modular architecture featuring:
- Game engine with turn-based system
- Event pool for game state changes
- Manipulator system for event routing
- Delivery system for I/O operations
- NPC and Player entities with autonomous behavior
- Spatial system with 2D positioning

## Identified Areas for Async Conversion

### 1. Game Loop (`game/engine.py`)
**Current State**: Synchronous infinite loop
```python
def game_loop(self):
    self._initialize_turn_queue()
    while 1:
        # Synchronous processing
```

**Recommended Change**: Convert to async generator
```python
async def game_loop_async(self) -> AsyncGenerator[GameState, None]:
    self._initialize_turn_queue()
    while self.running:
        # Process turn
        state_snapshot = self.get_serializable_state()
        yield state_snapshot
        await asyncio.sleep(turn_interval)
```

### 2. Event System (`game/event_pool.py`)
**Current State**: Synchronous event handling
**Recommended Change**: Async event bus with streaming
```python
class AsyncEventBus:
    def __init__(self):
        self.subscribers = []
        self.event_queue = asyncio.Queue()
    
    async def publish_event(self, event: Event):
        """Publish events to all subscribers asynchronously."""
        for subscriber in self.subscribers:
            await subscriber.receive_event(event)
    
    async def stream_events(self) -> AsyncGenerator[Event, None]:
        """Stream events to web clients."""
        while True:
            event = await self.event_queue.get()
            yield event
```

### 3. Delivery System (`interface/delivery.py`)
**Current State**: Synchronous terminal I/O
**Recommended Change**: WebSocket-based async delivery
```python
class WebSocketDelivery(Delivery):
    def __init__(self):
        super().__init__()
        self.websocket_connections = []
        self.action_queue = asyncio.Queue()
    
    async def broadcast_state_update(self, state: Dict):
        """Broadcast state updates to all connected clients."""
        for ws in self.websocket_connections:
            await ws.send_json(state)
    
    async def receive_player_action(self) -> str:
        """Receive player actions from web interface."""
        return await self.action_queue.get()
```

### 4. Manipulator System (`game/manipulator.py`)
**Current State**: Synchronous event processing
**Recommended Change**: Async event processing pipeline
```python
class AsyncManipulator:
    async def process_events_async(self, events: List[Event]) -> AsyncGenerator[ActionResult, None]:
        """Process events asynchronously and stream results."""
        for event in events:
            result = await self._execute_single_event_async(event)
            yield result
            await asyncio.sleep(0)  # Yield control to other coroutines
```

## Recommended Architecture Pattern

### 1. Event-Driven Architecture with Async Streams
- Implement an async event bus that streams game events to web clients
- Use Server-Sent Events (SSE) or WebSockets for real-time updates
- Create async generators for different types of game data streams

### 2. Microservice-like Structure
- **Game Engine Service**: Core game logic with async state streaming
- **Event Service**: Async event bus for real-time updates
- **Delivery Service**: Handle web interface communications
- **State Service**: Manage game state with async persistence

### 3. Async Generators for Different Data Streams

#### Game State Stream
```python
async def stream_game_state(session: Session) -> AsyncGenerator[Dict, None]:
    """Stream game state snapshots to web clients."""
    while session.running:
        state = session.get_serializable_state()
        yield format_for_web(state)
        await asyncio.sleep(STATE_UPDATE_INTERVAL)
```

#### Event Stream
```python
async def stream_events(event_bus: AsyncEventBus) -> AsyncGenerator[Dict, None]:
    """Stream game events to web clients."""
    async for event in event_bus.subscribe():
        yield event.to_dict()
```

#### Turn Stream
```python
async def stream_turn_updates(session: Session) -> AsyncGenerator[Dict, None]:
    """Stream turn-based updates to web clients."""
    previous_turn_state = None
    while session.running:
        current_turn_state = session.get_current_turn_state()
        if current_turn_state != previous_turn_state:
            yield current_turn_state
            previous_turn_state = current_turn_state
        await asyncio.sleep(TURN_CHECK_INTERVAL)
```

## Implementation Strategy

### Phase 1: Core Async Infrastructure
1. Create async versions of core services alongside sync versions
2. Implement async event bus
3. Develop async state serialization methods

### Phase 2: Delivery System Overhaul
1. Implement WebSocket delivery system
2. Create web interface endpoints
3. Add async broadcasting capabilities

### Phase 3: Game Loop Transformation
1. Convert game loop to async generator
2. Implement state snapshot streaming
3. Add pause/resume controls for web interface

### Phase 4: Client Integration
1. Develop web client to consume async streams
2. Implement real-time UI updates
3. Add controls for player actions

## Benefits of This Architecture

1. **Real-time Updates**: Web clients receive live game state updates
2. **Scalability**: Async architecture handles multiple concurrent clients efficiently
3. **Responsive UI**: Non-blocking operations ensure smooth user experience
4. **Flexibility**: Multiple simultaneous game sessions possible
5. **Observability**: Easy to monitor and debug game state changes

## Technical Considerations

1. **Concurrency Control**: Implement proper locking for shared state
2. **Error Handling**: Robust error handling for async operations
3. **Backward Compatibility**: Maintain sync interfaces during transition
4. **Performance**: Monitor async overhead and optimize critical paths
5. **Testing**: Develop async testing strategies

This architecture would transform MAGGxDND from a terminal-based game engine to a web-compatible system with real-time updates and responsive interfaces.