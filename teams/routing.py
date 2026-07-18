from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/channel/(?P<channel_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/dm/(?P<user_id>\d+)/$', consumers.DMConsumer.as_asgi()),
    re_path(r'ws/call/(?P<room_id>[0-9a-f-]+)/$', consumers.CallConsumer.as_asgi()),
]
