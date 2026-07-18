import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import teams.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zayro_teams.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(teams.routing.websocket_urlpatterns)
    ),
})
