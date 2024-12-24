from channels.generic.websocket import AsyncWebsocketConsumer
import json

class TeacherConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("teacher_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("teacher_group", self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            print(f"Received message: {data}")
        except json.JSONDecodeError:
            pass

    async def student_status(self, event):
        """处理学生状态更新"""
        print(f"Sending student status: {event}")
        message = {
            'type': 'student_login',  # 固定为 student_login 类型
            'student': {
                'student_id': event['data']['student_id'],
                'name': event['data']['name'],
                'ip': event['data']['ip'],
                'login_time': event['data']['last_login']
            }
        }
        await self.send(text_data=json.dumps(message)) 