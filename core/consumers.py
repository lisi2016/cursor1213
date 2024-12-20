from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
import json
from asgiref.sync import sync_to_async
from django.utils import timezone
from .models import User

class StudentStatusConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        print("WebSocket connection attempt")
        if self.scope["user"].is_authenticated and self.scope["user"].is_teacher:
            print(f"Teacher connected: {self.scope['user'].username}")
            await self.channel_layer.group_add("teacher_group", self.channel_name)
            await self.accept()
            
            # 发送当前在线学生列表
            online_students = await self.get_online_students()
            for student in online_students:
                await self.send_json({
                    "action": "login",
                    **student
                })
        else:
            print("Non-teacher connection rejected")
            await self.close()

    async def disconnect(self, close_code):
        print(f"WebSocket disconnected: {close_code}")
        await self.channel_layer.group_discard("teacher_group", self.channel_name)

    async def receive_json(self, content):
        print(f"Received message: {content}")
        pass

    async def student_status(self, event):
        print(f"Broadcasting student status: {event}")
        await self.send_json(event['data'])

    @sync_to_async
    def get_online_students(self):
        five_minutes_ago = timezone.now() - timezone.timedelta(minutes=5)
        students = User.objects.filter(
            is_teacher=False,
            last_login__gte=five_minutes_ago,
            ip_address__isnull=False
        )
        return [{
            'student_id': student.student_id,
            'name': student.first_name,
            'ip': student.ip_address,
            'last_login': student.last_login.strftime('%Y-%m-%d %H:%M:%S')
        } for student in students] 