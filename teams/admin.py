from django.contrib import admin
from .models import Team, TeamMember, Channel, Message, DirectMessage, CallSession

admin.site.register(Team)
admin.site.register(TeamMember)
admin.site.register(Channel)
admin.site.register(Message)
admin.site.register(DirectMessage)
admin.site.register(CallSession)
