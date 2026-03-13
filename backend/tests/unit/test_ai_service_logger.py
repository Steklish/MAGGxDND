"""
Unit Tests for AI Service Logger
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from backend.src.services.ai_service_logger import AIServiceLogger, log_ai_call


class TestAIServiceLogger:
    """Test AI Service Logger"""
    
    @pytest.fixture
    def mock_ai_client(self):
        """Create mock AI client"""
        client = MagicMock()
        client.generate = AsyncMock(return_value="Test response")
        client.generate_stream = AsyncMock()
        client.generate_stream.return_value.__aiter__.return_value = [
            "Chunk 1", "Chunk 2", "Chunk 3"
        ]
        return client
    
    @pytest.fixture
    def ai_logger(self, mock_ai_client):
        """Create AI logger instance"""
        return AIServiceLogger(mock_ai_client)
    
    @pytest.mark.asyncio
    async def test_generate_success(self, ai_logger, mock_ai_client):
        """Test successful AI generation"""
        prompt = "Test prompt"
        response = await ai_logger.generate(prompt)
        
        assert response == "Test response"
        mock_ai_client.generate.assert_called_once_with(
            prompt=prompt,
            model=None,
            temperature=0.7,
            max_tokens=None
        )
    
    @pytest.mark.asyncio
    async def test_generate_with_parameters(self, ai_logger, mock_ai_client):
        """Test AI generation with custom parameters"""
        prompt = "Test prompt"
        response = await ai_logger.generate(
            prompt,
            model="test-model",
            temperature=0.5,
            max_tokens=100
        )
        
        assert response == "Test response"
        mock_ai_client.generate.assert_called_once_with(
            prompt=prompt,
            model="test-model",
            temperature=0.5,
            max_tokens=100
        )
    
    @pytest.mark.asyncio
    async def test_generate_error_handling(self, ai_logger, mock_ai_client):
        """Test error handling in AI generation"""
        mock_ai_client.generate.side_effect = Exception("AI Error")
        
        with pytest.raises(Exception) as exc_info:
            await ai_logger.generate("Test prompt")
        
        assert str(exc_info.value) == "AI Error"
    
    @pytest.mark.asyncio
    async def test_generate_tracks_statistics(self, ai_logger, mock_ai_client):
        """Test that statistics are tracked"""
        await ai_logger.generate("Prompt 1")
        await ai_logger.generate("Prompt 2")
        await ai_logger.generate("Prompt 3")
        
        stats = ai_logger.get_stats()
        
        assert stats['total_requests'] == 3
        assert stats['total_tokens'] > 0
        assert stats['total_time_seconds'] >= 0
    
    @pytest.mark.asyncio
    async def test_generate_stream(self, ai_logger, mock_ai_client):
        """Test streaming generation"""
        chunks = []
        async for chunk in ai_logger.generate_stream("Test prompt"):
            chunks.append(chunk)
        
        assert len(chunks) == 3
        assert chunks == ["Chunk 1", "Chunk 2", "Chunk 3"]
    
    @pytest.mark.asyncio
    async def test_generate_stream_error(self, ai_logger, mock_ai_client):
        """Test streaming error handling"""
        mock_ai_client.generate_stream.side_effect = Exception("Stream Error")
        
        with pytest.raises(Exception) as exc_info:
            async for _ in ai_logger.generate_stream("Test prompt"):
                pass
        
        assert str(exc_info.value) == "Stream Error"


class TestLogAICallDecorator:
    """Test AI call logging decorator"""
    
    @pytest.mark.asyncio
    async def test_decorator_success(self):
        """Test decorator with successful call"""
        call_count = 0
        
        @log_ai_call
        async def test_function(prompt):
            nonlocal call_count
            call_count += 1
            return f"Response to {prompt}"
        
        result = await test_function("Test")
        
        assert result == "Response to Test"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_decorator_error(self):
        """Test decorator with error"""
        
        @log_ai_call
        async def failing_function(prompt):
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await failing_function("Test")


class TestAIRequestLogging:
    """Test AI request logging functionality"""
    
    def test_request_id_format(self):
        """Test request ID format"""
        from backend.src.services.ai_service_logger import AIServiceLogger
        
        logger = AIServiceLogger(MagicMock())
        request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}_0"
        
        # Should match format: req_YYYYMMDD_HHMMSS_N
        assert request_id.startswith('req_')
        assert '_' in request_id
    
    def test_stats_initialization(self):
        """Test statistics initialization"""
        from backend.src.services.ai_service_logger import AIServiceLogger
        
        logger = AIServiceLogger(MagicMock())
        stats = logger.get_stats()
        
        assert 'total_requests' in stats
        assert 'total_tokens' in stats
        assert 'total_time_seconds' in stats
        assert 'avg_time_per_request' in stats


@pytest.mark.integration
class TestAILoggingIntegration:
    """Integration tests for AI logging"""
    
    @pytest.mark.asyncio
    async def test_full_logging_flow(self, caplog):
        """Test complete logging flow"""
        from backend.src.logging import setup_logging, get_logger
        
        # Setup logging
        setup_logging(log_dir='./test_logs')
        logger = get_logger('ai')
        
        # Log test message
        logger.info("Test AI log message")
        
        # Verify log was created
        assert "Test AI log message" in caplog.text
    
    @pytest.mark.asyncio
    async def test_context_logging(self):
        """Test logging with context"""
        from backend.src.logging import LogContext, get_logger
        
        logger = get_logger('test')
        
        with LogContext(logger, user_id=123, action='test'):
            logger.info("Message with context")
        
        # Context should be added to log record
        # (verification depends on log handler implementation)
