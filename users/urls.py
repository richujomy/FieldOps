from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    
    # User profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    
    # Admin-only endpoints
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:user_id>/approve/', views.approve_field_worker, name='approve_field_worker'),
    path('users/<int:user_id>/reject/', views.reject_field_worker, name='reject_field_worker'),
    path('users/<int:user_id>/toggle-active/', views.activate_user, name='activate_user'),
]
