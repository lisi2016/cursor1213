from django.urls import re_path
from core.consumers import TeacherConsumer

# WebSocket 路由配置
websocket_urlpatterns = [
    re_path(r'ws/teacher/$', TeacherConsumer.as_asgi()),
] 