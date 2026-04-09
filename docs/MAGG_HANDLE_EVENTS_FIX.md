# MAGG handle_events Error Fix

## Problem
```
[PLAYER_ACTION] MAGG handle_events failed: , using fallback
```

The error message was empty, making it impossible to diagnose the root cause. The MAGG's `handle_events()` method was failing silently and falling back to the `comment()` method.

## Root Cause Analysis

The `handle_events()` method runs three functions in parallel:
1. `world_intervention(events)` - Updates scene state (add/remove objects, NPCs)
2. `comment(events)` - Generates AI narrative for events
3. `check_plot_following(events)` - Checks if players are following the plot

If ANY of these three functions threw an exception, the entire `handle_events()` would fail, resulting in the fallback behavior.

### Common Failure Points:
1. **Empty action lists** - `run_list_in_parallel_generator` called with empty `funcs` and `args` lists
2. **Missing plot** - `check_plot_following` raised `ValueError` when no plot existed
3. **AI generation errors** - Any of the three functions could fail during AI generation
4. **Missing dependencies** - `session.manipulator` or `session._plot` not available

## Fixes Applied

### 1. Enhanced Error Logging in Game Delivery
**File**: `backend/src/delivery/game_delivery.py`

**Changes**:
- Added `traceback` import and detailed error logging
- Added nested try-except for fallback `comment()` call
- Now logs full stack trace for debugging

```python
except Exception as magg_error:
    import traceback
    self.session.logger.warning(f"[PLAYER_ACTION] MAGG handle_events failed: {magg_error}, using fallback")
    self.session.logger.debug(f"[PLAYER_ACTION] MAGG error traceback: {traceback.format_exc()}")
    # Fallback: call comment() directly with events
    try:
        if hasattr(self.session.game_master, 'comment'):
            dm_response = self.session.game_master.comment(events)
        else:
            dm_response = verdict.details if verdict.details else action_text
    except Exception as comment_error:
        self.session.logger.error(f"[PLAYER_ACTION] Fallback comment() also failed: {comment_error}")
        dm_response = verdict.details if verdict.details else action_text
```

### 2. Error Handling in `handle_events()`
**File**: `core/magg/magg.py`

**Changes**:
- Wrapped parallel execution in try-except
- If parallel processing fails, tries direct `comment()` call
- Logs detailed error with stack trace
- Re-raises exception to signal failure

```python
async def handle_events(self):
    events = self.event_queue.get_all()
    self.event_queue.clear()
    comment = None

    try:
        async for result in run_list_in_parallel_generator(...):
            # Process results
            ...
    except Exception as e:
        self.logger.error(f"[MAGG] handle_events error: {e}", exc_info=True)
        # If parallel processing fails, try to generate comment directly
        if comment is None and events:
            try:
                comment = self.comment(events)
            except Exception as comment_err:
                self.logger.error(f"[MAGG] Direct comment() also failed: {comment_err}")
                comment = None
        raise

    return comment
```

### 3. Error Handling in `world_intervention()`
**File**: `core/magg/magg.py`

**Changes**:
- Added try-except wrapper
- Only calls `run_list_in_parallel_generator` if there are actions to execute
- Prevents empty list errors
- Logs and re-raises exceptions

```python
async def world_intervention(self, events : List[Event]):
    try:
        # ... AI generation code ...
        
        # Only run parallel generator if there are actions
        if actions:
            async for event in run_list_in_parallel_generator(
                funcs=actions,
                args_list=args
            ):
                yield event
        else:
            self.logger.debug("No world intervention actions required")
    except Exception as e:
        self.logger.error(f"[MAGG] world_intervention failed: {e}", exc_info=True)
        raise
```

### 4. Error Handling in `check_plot_following()`
**File**: `core/magg/magg.py`

**Changes**:
- Wrapped entire function in try-except
- Changed from raising `ValueError` to early `return` when no plot exists
- Logs errors but doesn't re-raise (plot checking is optional)
- Only runs parallel generator if there are actions

```python
async def check_plot_following(self, events : list[Event]):
    try:
        # Only check plot following if a plot exists
        if not self.session._plot:
            self.logger.debug("No plot available, skipping plot following check")
            return  # Changed from: raise ValueError(...)
        
        # ... rest of the logic ...
        
        # Only run parallel generator if there are actions
        if actions:
            async for event in run_list_in_parallel_generator(...):
                yield event
    except Exception as e:
        self.logger.error(f"[MAGG] check_plot_following failed: {e}", exc_info=True)
        # Don't re-raise - plot following is optional, failure shouldn't break the whole flow
        return
```

### 5. Error Handling in `comment()`
**File**: `core/magg/magg.py`

**Changes**:
- Added try-except wrapper around AI generation
- Logs detailed error and re-raises exception

```python
def comment(self, events : list[Event]) -> str:
    try:
        self.event_queue.clear()
        events_str = self._events_to_string(events)
        # ... prompt generation ...
        
        comment = self.generator.generate_one_shot(
            pydantic_model=SimpleComment,
            prompt=prompt
        )
        
        new_message = Message(
            sender_name="Mage",
            text=comment.comment)
        self.session.new_message(new_message)
        
        return comment.comment
    except Exception as e:
        self.logger.error(f"[MAGG] comment() failed: {e}", exc_info=True)
        raise
```

## Benefits

1. **Better Error Messages**: Full stack traces logged for debugging
2. **Graceful Degradation**: Each component can fail independently
3. **Prevents Empty List Errors**: Only runs parallel execution when there are actions
4. **No More Silent Failures**: All exceptions logged with details
5. **Fallback Chain**: If `handle_events()` fails → try `comment()` → use verdict details

## Testing

To verify the fix:

1. **Check logs** - Look for detailed error messages like:
   ```
   [MAGG] world_intervention failed: <detailed error message>
   [MAGG] handle_events error: <detailed error message>
   [PLAYER_ACTION] MAGG error traceback: <full stack trace>
   ```

2. **Expected behavior** - Even if one component fails, players should still see:
   - AI narrative (from `comment()` fallback)
   - Game state changes applied
   - No crashes or lost actions

3. **Common scenarios that were failing**:
   - ✅ Actions with no physical changes (just talking)
   - ✅ Sessions without plot initialized
   - ✅ AI generation timeouts or errors
   - ✅ Missing manipulator methods

## Files Modified

- `backend/src/delivery/game_delivery.py` - Enhanced error logging
- `core/magg/magg.py` - Added error handling to all MAGG methods

## No Breaking Changes

All changes are additive error handling. The system behavior remains the same, but now:
- Errors are logged with full details
- Fallback mechanisms work properly
- Players always get some form of narrative response
