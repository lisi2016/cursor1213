from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/student_status/$', consumers.StudentStatusConsumer.as_asgi()),
] 