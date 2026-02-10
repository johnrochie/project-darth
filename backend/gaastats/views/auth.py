"""
Authentication Views for GAA Stats App

Handles login, registration, password reset, and token generation
"""

from rest_framework import status, generics, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings

from ..models import UserProfile, Club
from ..serializers import UserProfileSerializer

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """Login serializer"""

    email = serializers.EmailField()
    password = serializers.CharField()
    subdomain = serializers.CharField(required=False, default='demo')


class RegisterSerializer(serializers.Serializer):
    """Registration serializer"""

    email = serializers.EmailField()
    password = serializers.CharField(min_length=8)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    club_subdomain = serializers.CharField(max_length=100)
    role = serializers.ChoiceField(choices=['viewer', 'admin'])


class PasswordResetSerializer(serializers.Serializer):
    """Password reset request serializer"""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Password reset confirmation serializer"""

    token = serializers.CharField()
    uid = serializers.CharField()
    new_password = serializers.CharField(min_length=8)


@api_view(['POST'])
@permission_classes([AllowAny])
def auth_login(request):
    """
    Handle user login (for web dashboard)

    Returns session cookie for web, or token for iPad app
    """

    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    subdomain = serializer.validated_data.get('subdomain', 'demo')

    # Authenticate user
    user = authenticate(username=email, password=password)

    if not user:
        return Response(
            {'error': 'Invalid email or password'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Get user profile to verify club access
    try:
        user_profile = UserProfile.objects.get(user=user)

        # Verify user belongs to the requested subdomain's club
        if user_profile.club.subdomain != subdomain:
            return Response(
                {'error': 'User does not belong to this club'},
                status=status.HTTP_403_FORBIDDEN
            )

    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Log in user (creates session)
    login(request, user)

    # Return user info
    return Response({
        'success': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user_profile.role,
            'club_id': user_profile.club.id,
            'club_name': user_profile.club.name,
            'club_subdomain': user_profile.club.subdomain,
        }
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def auth_register(request):
    """
    Handle user registration

    Note: In production, may require admin invitation or approval
    """

    serializer = RegisterSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    first_name = serializer.validated_data['first_name']
    last_name = serializer.validated_data['last_name']
    club_subdomain = serializer.validated_data['club_subdomain']
    role = serializer.validated_data['role']

    # Check if club exists
    try:
        club = Club.objects.get(subdomain=club_subdomain)
    except Club.DoesNotExist:
        return Response(
            {'error': 'Club not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check if user already exists
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'Email already registered'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create user
    try:
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Create user profile
        user_profile = UserProfile.objects.create(
            user=user,
            club=club,
            role=role
        )

        # Log in user
        login(request, user)

        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user_profile.role,
                'club_id': user_profile.club.id,
                'club_name': user_profile.club.name,
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def auth_logout(request):
    """Handle user logout (for web dashboard)"""

    logout(request)

    return Response({
        'success': True,
        'message': 'Logged out successfully'
    })


@api_view(['GET'])
def auth_me(request):
    """Get current authenticated user info"""

    if not request.user.is_authenticated:
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        user_profile = UserProfile.objects.get(user=request.user)

        return Response({
            'user': {
                'id': request.user.id,
                'email': request.user.email,
                'username': request.user.username,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'role': user_profile.role,
                'club_id': user_profile.club.id,
                'club_name': user_profile.club.name,
                'club_subdomain': user_profile.club.subdomain,
            }
        })

    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset(request):
    """
    Request password reset

    Sends email with password reset link
    """

    serializer = PasswordResetSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email']

    # Check if user exists
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Return success even if email doesn't exist (security)
        return Response({
            'success': True,
            'message': 'If an account exists with that email, a password reset link has been sent'
        })

    # Generate password reset token
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    # Build reset URL
    current_site = get_current_site(request)
    reset_url = f"https://{current_site.domain}/auth/reset-password/{uid}/{token}/"

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
            settings.DEFAULT_FROM_EMAIL,  # Will need to set this
            [email],
            fail_silently=False
        )

        return Response({
            'success': True,
            'message': 'Password reset email sent'
        })

    except Exception as e:
        return Response(
            {'error': f'Failed to send email: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """
    Confirm password reset

    Sets new password with valid token
    """

    serializer = PasswordResetConfirmSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    token = serializer.validated_data['token']
    uid = serializer.validated_data['uid']
    new_password = serializer.validated_data['new_password']

    # Decode user ID
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, User.DoesNotExist):
        return Response(
            {'error': 'Invalid reset link'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify token
    if not default_token_generator.check_token(user, token):
        return Response(
            {'error': 'Invalid or expired reset link'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Set new password
    try:
        user.set_password(new_password)
        user.save()

        return Response({
            'success': True,
            'message': 'Password reset successfully'
        })

    except Exception as e:
        return Response(
            {'error': f'Failed to reset password: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
