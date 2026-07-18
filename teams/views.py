from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Max
from django.utils import timezone
from django.conf import settings as django_settings
from .models import Team, TeamMember, Channel, Message, DirectMessage, CallSession, ScheduledMeeting
from accounts.models import User, Invitation
from accounts.forms import InviteForm
import uuid


@login_required
def dashboard(request):
    teams = request.user.teams.all()
    dms = DirectMessage.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-created_at')

    dm_users = {}
    for dm in dms:
        other = dm.receiver if dm.sender == request.user else dm.sender
        if other.id not in dm_users:
            dm_users[other.id] = {'user': other, 'last_msg': dm}

    return render(request, 'teams/dashboard.html', {
        'teams': teams,
        'dm_users': list(dm_users.values())[:10],
    })


@login_required
def team_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if name:
            team = Team.objects.create(name=name, description=description, created_by=request.user)
            TeamMember.objects.create(team=team, user=request.user, role=TeamMember.ROLE_ADMIN)
            Channel.objects.create(team=team, name='general', channel_type=Channel.TYPE_TEXT)
            Channel.objects.create(team=team, name='voice', channel_type=Channel.TYPE_VOICE)
            messages.success(request, f'Team "{name}" created!')
            return redirect('teams:team_detail', pk=team.pk)
    return render(request, 'teams/team_form.html')


@login_required
def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if not team.members.filter(pk=request.user.pk).exists():
        messages.error(request, 'You are not a member of this team.')
        return redirect('teams:dashboard')
    channels = team.channels.all()
    members = team.teammember_set.select_related('user').all()
    return render(request, 'teams/team_detail.html', {
        'team': team, 'channels': channels, 'members': members,
    })


@login_required
def channel_view(request, team_pk, channel_pk):
    team = get_object_or_404(Team, pk=team_pk)
    channel = get_object_or_404(Channel, pk=channel_pk, team=team)
    if not team.members.filter(pk=request.user.pk).exists():
        return redirect('teams:dashboard')
    msgs = channel.messages.select_related('sender').order_by('created_at')
    return render(request, 'teams/channel.html', {
        'team': team, 'channel': channel, 'messages': msgs,
    })


@login_required
def invite_member(request, team_pk):
    team = get_object_or_404(Team, pk=team_pk)
    member = TeamMember.objects.filter(team=team, user=request.user, role=TeamMember.ROLE_ADMIN).first()
    if not member:
        messages.error(request, 'Only admins can invite members.')
        return redirect('teams:team_detail', pk=team_pk)

    form = InviteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        invite = Invitation.objects.create(email=email, invited_by=request.user, team=team)
        base = getattr(django_settings, 'SITE_URL', request.build_absolute_uri('/').rstrip('/'))
        invite_url = f"{base}/accounts/invite/{invite.token}/"
        messages.success(request, f'Invitation sent to {email}. Link: {invite_url}')
        return redirect('teams:team_detail', pk=team_pk)
    return render(request, 'teams/invite.html', {'form': form, 'team': team})


@login_required
def dm_view(request, user_pk):
    other = get_object_or_404(User, pk=user_pk)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            DirectMessage.objects.create(sender=request.user, receiver=other, content=content)
        return redirect('teams:dm', user_pk=user_pk)

    DirectMessage.objects.filter(sender=other, receiver=request.user, is_read=False).update(is_read=True)
    msgs = DirectMessage.objects.filter(
        Q(sender=request.user, receiver=other) | Q(sender=other, receiver=request.user)
    ).order_by('created_at')
    users = User.objects.exclude(pk=request.user.pk)
    return render(request, 'teams/dm.html', {'other': other, 'messages': msgs, 'users': users})


@login_required
def start_call(request, user_pk):
    other = get_object_or_404(User, pk=user_pk)
    call_type = request.GET.get('type', 'video')
    session = CallSession.objects.create(
        call_type=call_type,
        initiator=request.user,
        status=CallSession.STATUS_CALLING,
    )
    session.participants.add(request.user, other)
    return redirect('teams:call_room', room_id=session.room_id)


@login_required
def schedule_list(request):
    meetings = ScheduledMeeting.objects.filter(created_by=request.user).order_by('scheduled_at')
    return render(request, 'teams/schedule_list.html', {'meetings': meetings})


@login_required
def schedule_create(request):
    teams = request.user.teams.all()
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        scheduled_at = request.POST.get('scheduled_at', '').strip()
        call_type = request.POST.get('call_type', 'video')
        team_id = request.POST.get('team_id') or None
        if title and scheduled_at:
            team = Team.objects.get(pk=team_id) if team_id else None
            meeting = ScheduledMeeting.objects.create(
                title=title,
                description=description,
                scheduled_at=scheduled_at,
                call_type=call_type,
                created_by=request.user,
                team=team,
            )
            return redirect('teams:schedule_detail', token=meeting.token)
    return render(request, 'teams/schedule_create.html', {'teams': teams})


@login_required
def schedule_detail(request, token):
    meeting = get_object_or_404(ScheduledMeeting, token=token)
    base = getattr(django_settings, 'SITE_URL', request.build_absolute_uri('/').rstrip('/'))
    invite_url = f"{base}/teams/schedule/join/{meeting.token}/"
    return render(request, 'teams/schedule_detail.html', {'meeting': meeting, 'invite_url': invite_url})


def schedule_join(request, token):
    meeting = get_object_or_404(ScheduledMeeting, token=token)
    if not request.user.is_authenticated:
        request.session['join_meeting'] = str(token)
        return redirect(f'/accounts/login/?next=/teams/schedule/join/{token}/')
    session, _ = CallSession.objects.get_or_create(
        room_id=meeting.room_id,
        defaults={
            'call_type': meeting.call_type,
            'initiator': request.user,
            'status': CallSession.STATUS_ACTIVE,
        }
    )
    session.participants.add(request.user)
    return redirect('teams:call_room', room_id=meeting.room_id)


@login_required
def call_room(request, room_id):
    session = get_object_or_404(CallSession, room_id=room_id)
    if request.user not in session.participants.all():
        messages.error(request, 'You are not part of this call.')
        return redirect('teams:dashboard')
    if session.status == CallSession.STATUS_CALLING and request.user != session.initiator:
        session.status = CallSession.STATUS_ACTIVE
        session.save()
    return render(request, 'teams/call_room.html', {'session': session, 'room_id': str(room_id)})
