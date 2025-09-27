from rest_framework import serializers
from .models import ServiceRequest




class ServiceRequestListSerializer(serializers.ModelSerializer):
    assigned_field_worker = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = ServiceRequest
        fields = (
            'id', 'assigned_field_worker', 'description', 'location', 'urgency', 'status',
            'rating', 'created_at'
        )
        read_only_fields = ('id', 'assigned_field_worker', 'status', 'rating', 'created_at')


class ServiceRequestDetailSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(read_only=True)
    assigned_field_worker = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ServiceRequest
        fields = (
            'id', 'customer', 'assigned_field_worker', 'description', 'location', 'urgency',
            'status', 'rating', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'customer', 'assigned_field_worker', 'status', 'rating', 'created_at', 'updated_at'
        )


class ServiceRequestCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequest
        fields = ('description', 'location', 'urgency')

    def create(self, validated_data):
        request = self.context.get('request')
        customer = getattr(request, 'user', None)
        return ServiceRequest.objects.create(customer=customer, **validated_data)

    def validate(self, attrs):
        # Keep validation minimal and practical
        return attrs


class ServiceRequestRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequest
        fields = ('rating',)

    def validate_rating(self, value: int):
        if value is None:
            return value
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value


class ServiceRequestAssignmentSerializer(serializers.ModelSerializer):
    assigned_field_worker = serializers.IntegerField(
        help_text="ID of the field worker to assign",
        allow_null=True,
        required=False
    )
    
    class Meta:
        model = ServiceRequest
        fields = ('assigned_field_worker',)
    
    def validate_assigned_field_worker(self, value):
        if value is None:
            return value
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('User does not exist.')
        
        if not user.is_field_worker:
            raise serializers.ValidationError('User must be a field worker.')
        if not user.is_approved:
            raise serializers.ValidationError('Field worker must be approved.')
        return value


