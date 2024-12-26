from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging

logger = logging.getLogger(__name__)

class TeacherConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            await self.channel_layer.group_add("teacher_group", self.channel_name)
            await self.accept()
            logger.info(f"Teacher WebSocket connected: {self.channel_name}")
        except Exception as e:
            logger.error(f"Error in connect: {str(e)}")

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard("teacher_group", self.channel_name)
            logger.info(f"Teacher WebSocket disconnected: {self.channel_name}")
        except Exception as e:
            logger.error(f"Error in disconnect: {str(e)}")

    async def student_status(self, event):
        """处理学生状态更新"""
        try:
            logger.info(f"Received student_status event: {event}")
            
            # 构建消息
            message = {
                'type': 'student_login',
                'student': {
                    'student_id': event['data']['student_id'],
                    'name': event['data']['name'],
                    'ip': event['data']['ip'],
                    'login_time': event['data']['last_login']
                }
            }
            
            # 发送消息到WebSocket客户端
            await self.send(text_data=json.dumps(message))
            logger.info(f"Sent message to client: {message}")
            
        except Exception as e:
            logger.error(f"Error in student_status: {str(e)}") 