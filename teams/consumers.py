import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.room_group = f'channel_{self.channel_id}'
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        user = self.scope['user']
        if not user.is_authenticated:
            return
        content = data.get('message', '').strip()
        if not content:
            return
        msg = await self.save_message(user, content)
        await self.channel_layer.group_send(self.room_group, {
            'type': 'chat_message',
            'message': content,
            'sender': user.display_name,
            'sender_id': user.pk,
            'avatar': user.avatar.url if user.avatar else '',
            'timestamp': msg.created_at.strftime('%H:%M'),
        })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_message(self, user, content):
        from .models import Message, Channel
        channel = Channel.objects.get(pk=self.channel_id)
        return Message.objects.create(channel=channel, sender=user, content=content)


class DMConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        other_id = self.scope['url_route']['kwargs']['user_id']
        ids = sorted([user.pk, int(other_id)])
        self.room_group = f'dm_{ids[0]}_{ids[1]}'
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        user = self.scope['user']
        if not user.is_authenticated:
            return
        content = data.get('message', '').strip()
        other_id = self.scope['url_route']['kwargs']['user_id']
        if not content:
            return
        msg = await self.save_dm(user, other_id, content)
        await self.channel_layer.group_send(self.room_group, {
            'type': 'dm_message',
            'message': content,
            'sender': user.display_name,
            'sender_id': user.pk,
            'avatar': user.avatar.url if user.avatar else '',
            'timestamp': msg.created_at.strftime('%H:%M'),
        })

    async def dm_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_dm(self, sender, receiver_id, content):
        from .models import DirectMessage
        from accounts.models import User
        receiver = User.objects.get(pk=receiver_id)
        return DirectMessage.objects.create(sender=sender, receiver=receiver, content=content)


class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group = f'call_{self.room_id}'
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()
        user = self.scope['user']
        await self.channel_layer.group_send(self.room_group, {
            'type': 'call_signal',
            'signal_type': 'user_joined',
            'user_id': user.pk,
            'user_name': user.display_name,
        })

    async def disconnect(self, code):
        user = self.scope['user']
        await self.channel_layer.group_send(self.room_group, {
            'type': 'call_signal',
            'signal_type': 'user_left',
            'user_id': user.pk,
            'user_name': user.display_name,
        })
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        user = self.scope['user']
        await self.channel_layer.group_send(self.room_group, {
            'type': 'call_signal',
            **data,
            'from_user': user.pk,
        })

    async def call_signal(self, event):
        await self.send(text_data=json.dumps(event))
