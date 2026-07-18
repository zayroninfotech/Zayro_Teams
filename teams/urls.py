from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('create/', views.team_create, name='team_create'),
    path('<int:pk>/', views.team_detail, name='team_detail'),
    path('<int:team_pk>/channels/<int:channel_pk>/', views.channel_view, name='channel'),
    path('<int:team_pk>/invite/', views.invite_member, name='invite_member'),
    path('dm/<int:user_pk>/', views.dm_view, name='dm'),
    path('call/<int:user_pk>/', views.start_call, name='start_call'),
    path('room/<uuid:room_id>/', views.call_room, name='call_room'),
]
