from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import User, Invitation
from .forms import RegisterForm, LoginForm, ProfileForm, InviteForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('teams:dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f'Welcome to Zayro Teams, {user.display_name}!')
        return redirect('teams:dashboard')
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('teams:dashboard')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(request, email=form.cleaned_data['email'], password=form.cleaned_data['password'])
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'teams:dashboard'))
        messages.error(request, 'Invalid email or password.')
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'form': form})


def accept_invitation(request, token):
    invite = get_object_or_404(Invitation, token=token, status=Invitation.STATUS_PENDING)
    if invite.expires_at and invite.expires_at < timezone.now():
        messages.error(request, 'This invitation has expired.')
        return redirect('accounts:login')

    if request.user.is_authenticated:
        invite.status = Invitation.STATUS_ACCEPTED
        invite.save()
        if invite.team:
            from teams.models import TeamMember
            TeamMember.objects.get_or_create(team=invite.team, user=request.user)
        messages.success(request, f'You joined {invite.team.name if invite.team else "Zayro Teams"}!')
        return redirect('teams:dashboard')

    # Store token in session so we can finalize after registration/login
    request.session['pending_invite'] = str(token)
    return render(request, 'accounts/accept_invite.html', {'invite': invite})
