from channels.middleware import BaseMiddleware
from channels.exceptions import StopConsumer
import logging

logger = logging.getLogger(__name__)

class WebSocketErrorMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        try:
            return await super().__call__(scope, receive, send)
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            raise StopConsumer() 