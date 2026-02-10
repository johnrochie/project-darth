"""
Authentication for GAA Stats Web Dashboard
Django session-based authentication (not token-based like iPad app)
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator, default_token_generator as password_reset_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings

from ..models import UserProfile, Club

User = get_user_model()


def login_user(request):
    """
    Handle web dashboard login (email/password)
    """

    if request.user.is_authenticated:
        return redirect('dashboard/')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        subdomain = request.headers.get('Host', '').split('.')[0]

        subdomain = 'demo' if not subdomain or subdomain == 'www' else subdomain

        # Authenticate user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Check if user belongs to this club
            try:
                profile = UserProfile.objects.get(user=user)

                # Verify club subdomain
                if profile.club.subdomain != subdomain:
                    messages.error(request, 'You are not authorized to access this club.')
                    return render(request, 'auth/login.html', {
                        'subdomain': subdomain,
                        'email': email,
                    })
            except UserProfile.DoesNotExist:
                messages.error(
                    request,
                    'Your account is not part of this club. Please contact your club admin.'
                )
                return render(request, 'auth/login.html', {
                    'subdomain': subdomain,
                    'email': email,
                })

            # Log in user (Django sessions)
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('dashboard/')

        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'auth/login.html', {
        'subdomain': subdomain,
        'email': request.POST.get('email', ''),
    })


def logout_user(request):
    """Handle logout"""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('/auth/login/')  # Redirect to login after logout


def register(request):
    """
    Handle registration (typically via invitation or admin-only in MVP)
    For MVP, registration may be disabled
    """
    messages.info(request, 'Registration is currently disabled. Please contact your club admin.')
    return render(request, 'auth/registration-disabled.html')


@login_required
def me_user(request):
    """
    Get current user info (for session validation)
    This is an API endpoint-like view for XHR requests
    """
    profile = UserProfile.objects.get(user=request.user)

    return {
        'id': request.user.id,
        'email': request.user.email,
        'username': request.user.username,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'role': profile.role,
        'club_id': profile.club.id,
        'club_name': profile.club.name,
        'club_subdomain': profile.club.subdomain,
    }


def password_reset_request(request):
    """
    Request password reset (sends email with reset link)
    """
    if request.method == 'POST':
        email = request.POST.get('email')

        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Return success even if user doesn't exist (security)
            return render(request, 'auth/password-reset-sent.html')

        # Generate password reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Build reset URL
        current_site = get_current_site(request)
        # For web dashboard, use HTTP (not HTTPS) for dev
        reset_url = f"{current_site.domain}/auth/password-reset/{uid}/{token}/"

        # Send email
        subject = 'GAA Stats Password Reset'
        message = f'''
        Click the link below to reset your password:

        {reset_url}

        If you did not request this, please ignore this email.
        '''

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,  # Will need to set this in settings
                [email],
                fail_silently=False
            )
            return render(request, 'auth/password-reset-sent.html')
        except Exception as e:
            # Fall back to console if email fails (development)
            print(f"Failed to send email: {e}")
            return render(request, 'auth/password-reset-sent.html')

    return render(request, 'auth/password-reset.html', {'email': request.GET.get('email', '')})


def password_reset_confirm(request, uidb64, token):
    """
    Confirm password reset (set new password)
    """
    if request.method == 'POST':
        password = request.POST.get('new_password')
        password2 = request.POST.get('new_password_confirm')

        if password != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/password-reset-confirm.html', {'validlink': False, 'form': True})

        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'auth/password-reset-confirm.html', {'validlink': False, 'form': True, 'uidb64': uidb64, 'token': token})

        # Decode user ID
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, User.DoesNotExist):
            return render(request, 'auth/password-reset-confirm.html', {'validlink': False})

        # Verify token
        if not default_token_generator.check_token(user, token):
            return render(request, 'auth/password-reset-confirm.html', {'validlink': False})

        # Set new password
        try:
            user.set_password(password)
            messages.success(request, 'Password has been reset. You can now login.')
            return redirect('/auth/login/')
        except Exception as e:
            messages.error(request, 'Failed to reset password. Please try again.')

    # For GET request, show reset form (already handling above)
    return render(request, 'auth/password-reset-confirm.html', {
        'uidb64': uidb64,
        'token': token,
        'validlink': True,
        'form': False,
    })
