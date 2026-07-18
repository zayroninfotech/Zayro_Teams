from django.db import models
from django.conf import settings
import uuid


class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='team_avatars/', null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_teams')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through='TeamMember', related_name='teams')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    ROLE_ADMIN = 'admin'
    ROLE_MEMBER = 'member'
    ROLE_CHOICES = [(ROLE_ADMIN, 'Admin'), (ROLE_MEMBER, 'Member')]

    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('team', 'user')


class Channel(models.Model):
    TYPE_TEXT = 'text'
    TYPE_VOICE = 'voice'
    TYPE_CHOICES = [(TYPE_TEXT, 'Text'), (TYPE_VOICE, 'Voice')]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='channels')
    name = models.CharField(max_length=100)
    channel_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_TEXT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"#{self.name} ({self.team.name})"


class DirectMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_dms')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_dms')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender} -> {self.receiver}: {self.content[:30]}"


class Message(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender} in #{self.channel.name}: {self.content[:30]}"


class CallSession(models.Model):
    TYPE_AUDIO = 'audio'
    TYPE_VIDEO = 'video'
    TYPE_CHOICES = [(TYPE_AUDIO, 'Audio'), (TYPE_VIDEO, 'Video')]

    STATUS_CALLING = 'calling'
    STATUS_ACTIVE = 'active'
    STATUS_ENDED = 'ended'
    STATUS_CHOICES = [
        (STATUS_CALLING, 'Calling'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_ENDED, 'Ended'),
    ]

    room_id = models.UUIDField(default=uuid.uuid4, unique=True)
    call_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_VIDEO)
    initiator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='initiated_calls')
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='call_sessions')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_CALLING)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
