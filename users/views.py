from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import authenticate
# from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import User
from .serializers import (
    UserRegistrationSerializer, 
    UserProfileSerializer, 
    UserLoginSerializer,
    UserListSerializer
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom login view that returns user data along with tokens.
    """
    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserProfileSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRegistrationView(generics.CreateAPIView):
    """
    User registration endpoint.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserProfileSerializer(user).data,
                'message': 'User registered successfully.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    User profile view (get/update own profile).
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UserListView(generics.ListAPIView):
    """
    List all users (admin only).
    """
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only admins can see all users
        if self.request.user.is_admin:
            return User.objects.all()
        return User.objects.none()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approve_field_worker(request, user_id):
    """
    Approve a field worker (admin only).
    """
    if not request.user.is_admin:
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id, role='field_worker')
        user.is_approved = True
        user.save()
        return Response({'message': 'Field worker approved successfully.'})
    except User.DoesNotExist:
        return Response({'error': 'Field worker not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reject_field_worker(request, user_id):
    """
    Reject a field worker (admin only).
    """
    if not request.user.is_admin:
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id, role='field_worker')
        user.is_approved = False
        user.save()
        return Response({'message': 'Field worker rejected.'})
    except User.DoesNotExist:
        return Response({'error': 'Field worker not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def activate_user(request, user_id):
    """
    Activate/deactivate a user (admin only).
    """
    if not request.user.is_admin:
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()
        status_text = 'activated' if user.is_active else 'deactivated'
        return Response({'message': f'User {status_text} successfully.'})
    except User.DoesNotExist:
        return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
