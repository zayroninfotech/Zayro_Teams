from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Invitation


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_online', 'is_staff')
    search_fields = ('email', 'username')
    ordering = ('email',)
    fieldsets = UserAdmin.fieldsets + (('Profile', {'fields': ('avatar', 'bio', 'is_online')}),)


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'invited_by', 'team', 'status', 'created_at')
    list_filter = ('status',)
