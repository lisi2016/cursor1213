from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging

logger = logging.getLogger(__name__)

class TeacherConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            await self.channel_layer.group_add(
                "teacher_group",
                self.channel_name
            )
            await self.accept()
            logger.info("Teacher WebSocket connection established")
        except Exception as e:
            logger.error(f"Error in connect: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(
                "teacher_group",
                self.channel_name
            )
            logger.info(f"Teacher WebSocket disconnected with code: {close_code}")
        except Exception as e:
            logger.error(f"Error in disconnect: {str(e)}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            await self.channel_layer.group_send(
                "teacher_group",
                {
                    'type': 'student_status',
                    'message': text_data_json
                }
            )
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")

    async def student_status(self, event):
        """处理学生状态更新消息"""
        try:
            await self.send(text_data=json.dumps(event['message']))
        except Exception as e:
            logger.error(f"Error in student_status: {str(e)}")

    async def student_login(self, event):
        """处理学生登录事件"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'student_login',
                'student': event['student']
            }))
            logger.info("Student login message sent to WebSocket")
        except Exception as e:
            logger.error(f"Error in student_login: {str(e)}") 