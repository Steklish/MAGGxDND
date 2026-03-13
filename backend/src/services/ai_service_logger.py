"""
AI Service with Comprehensive Logging
Logs all AI interactions including full requests and responses
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import json
import time
from pathlib import Path

from backend.src.logging import get_logger, LogContext
from backend.src.config import settings

logger = get_logger('ai')
request_logger = get_logger('ai.requests')
response_logger = get_logger('ai.responses')


class AIServiceLogger:
    """
    Wrapper for AI service that provides comprehensive logging
    of all AI interactions
    """
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
        self.request_count = 0
        self.total_tokens = 0
        self.total_time = 0.0
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate AI response with full logging
        
        Args:
            prompt: Input prompt
            model: Model to use (default from settings)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
        
        Returns:
            Generated text
        """
        start_time = time.time()
        request_id = f"req_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{self.request_count}"
        
        # Log request start
        logger.info(
            f"🤖 AI Generation Started [{request_id}]",
            extra={
                'request_id': request_id,
                'model': model or settings.GEMINI_MODEL,
                'prompt_length': len(prompt),
                'prompt_preview': prompt[:200].replace('\n', ' '),
                'temperature': temperature,
                'max_tokens': max_tokens
            }
        )
        
        # Log full request to dedicated file
        request_data = {
            'request_id': request_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'model': model or settings.GEMINI_MODEL,
            'prompt': prompt,
            'parameters': {
                'temperature': temperature,
                'max_tokens': max_tokens,
                **kwargs
            }
        }
        
        request_logger.info(json.dumps(request_data, ensure_ascii=False, indent=2))
        
        # Log to console (truncated)
        print(f"🤖 [AI Request {request_id}]")
        print(f"   Model: {model or settings.GEMINI_MODEL}")
        print(f"   Prompt: {prompt[:100]}...")
        print(f"   Length: {len(prompt)} chars")
        
        try:
            # Generate response
            response = await self.ai_client.generate(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Calculate metrics
            processing_time = time.time() - start_time
            response_length = len(response) if response else 0
            estimated_tokens = response_length // 4  # Rough estimate
            
            self.request_count += 1
            self.total_tokens += estimated_tokens
            self.total_time += processing_time
            
            # Log success
            logger.info(
                f"✅ AI Generation Complete [{request_id}]",
                extra={
                    'request_id': request_id,
                    'response_length': response_length,
                    'estimated_tokens': estimated_tokens,
                    'processing_time_ms': round(processing_time * 1000, 2),
                    'response_preview': response[:200].replace('\n', ' ') if response else None
                }
            )
            
            # Log full response
            response_data = {
                'request_id': request_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'success': True,
                'response': response,
                'metrics': {
                    'response_length': response_length,
                    'estimated_tokens': estimated_tokens,
                    'processing_time_ms': round(processing_time * 1000, 2)
                }
            }
            
            response_logger.info(json.dumps(response_data, ensure_ascii=False, indent=2))
            
            # Console output
            print(f"✅ [AI Response {request_id}]")
            print(f"   Length: {response_length} chars")
            print(f"   Time: {processing_time*1000:.2f}ms")
            print(f"   Preview: {response[:100]}...")
            print()
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"❌ AI Generation Failed [{request_id}]",
                extra={
                    'request_id': request_id,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'processing_time_ms': round(processing_time * 1000, 2)
                },
                exc_info=True
            )
            
            # Log failed request
            error_data = {
                'request_id': request_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'prompt': prompt[:500]  # Include partial prompt for debugging
            }
            
            response_logger.error(json.dumps(error_data, ensure_ascii=False, indent=2))
            
            # Console output
            print(f"❌ [AI Error {request_id}]")
            print(f"   Error: {str(e)}")
            print(f"   Type: {type(e).__name__}")
            print()
            
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ):
        """
        Generate streaming AI response with logging
        
        Yields:
            Chunks of generated text
        """
        request_id = f"stream_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{self.request_count}"
        
        logger.info(
            f"🌊 AI Stream Started [{request_id}]",
            extra={
                'request_id': request_id,
                'model': model or settings.GEMINI_MODEL,
                'prompt_length': len(prompt)
            }
        )
        
        try:
            chunk_count = 0
            total_chars = 0
            
            async for chunk in self.ai_client.generate_stream(
                prompt=prompt,
                model=model,
                **kwargs
            ):
                chunk_count += 1
                total_chars += len(chunk)
                
                # Log every 10th chunk to avoid spam
                if chunk_count % 10 == 0:
                    logger.debug(
                        f"Stream progress [{request_id}]",
                        extra={
                            'chunks': chunk_count,
                            'chars': total_chars
                        }
                    )
                
                yield chunk
            
            logger.info(
                f"✅ AI Stream Complete [{request_id}]",
                extra={
                    'request_id': request_id,
                    'total_chunks': chunk_count,
                    'total_chars': total_chars
                }
            )
            
        except Exception as e:
            logger.error(
                f"❌ AI Stream Failed [{request_id}]",
                extra={
                    'request_id': request_id,
                    'error': str(e)
                },
                exc_info=True
            )
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get AI usage statistics"""
        return {
            'total_requests': self.request_count,
            'total_tokens': self.total_tokens,
            'total_time_seconds': round(self.total_time, 2),
            'avg_time_per_request': round(self.total_time / max(self.request_count, 1), 2)
        }


# Decorator for logging AI calls
def log_ai_call(func):
    """
    Decorator to log AI function calls
    
    Usage:
        @log_ai_call
        async def my_ai_function(prompt):
            ...
    """
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        request_id = f"decorator_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(
            f"🔹 AI Function Call [{request_id}]",
            extra={
                'request_id': request_id,
                'function': func.__name__,
                'args_count': len(args),
                'kwargs_count': len(kwargs)
            }
        )
        
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            
            processing_time = time.time() - start_time
            
            logger.info(
                f"✅ AI Function Complete [{request_id}]",
                extra={
                    'request_id': request_id,
                    'function': func.__name__,
                    'processing_time_ms': round(processing_time * 1000, 2)
                }
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            logger.error(
                f"❌ AI Function Failed [{request_id}]",
                extra={
                    'request_id': request_id,
                    'function': func.__name__,
                    'error': str(e),
                    'processing_time_ms': round(processing_time * 1000, 2)
                },
                exc_info=True
            )
            raise
    
    return wrapper
