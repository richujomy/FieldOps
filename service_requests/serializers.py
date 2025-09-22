from rest_framework import serializers
from .models import ServiceRequest


class ServiceRequestListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequest
        fields = (
            'id', 'description', 'location', 'urgency', 'status',
            'rating', 'created_at'
        )
        read_only_fields = ('id', 'status', 'rating', 'created_at')


class ServiceRequestDetailSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ServiceRequest
        fields = (
            'id', 'customer', 'description', 'location', 'urgency',
            'status', 'rating', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'customer', 'status', 'rating', 'created_at', 'updated_at'
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


