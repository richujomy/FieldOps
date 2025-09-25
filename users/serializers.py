from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'role', 'phone_number')
        extra_kwargs = {
            'role': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        
        # Field workers must provide phone number
        if attrs.get('role') == 'field_worker' and not attrs.get('phone_number'):
            raise serializers.ValidationError("Phone number is required for field workers.")
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        role = validated_data.get('role')
        user = User.objects.create_user(password=password, **validated_data)
        # only field worker requires approval
        if role != 'field_worker':
            user.is_approved = True
            user.save(update_fields=["is_approved"])
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile (read/update).
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone_number', 'is_approved', 'is_active', 'date_joined')
        read_only_fields = ('id', 'username', 'role', 'is_approved', 'is_active', 'date_joined')


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include username and password.')


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users (admin only).
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_approved', 'is_active', 'date_joined')
