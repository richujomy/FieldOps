from rest_framework import serializers
from .models import Task


class TaskListSerializer(serializers.ModelSerializer):
    service_request_description = serializers.CharField(source='service_request.description', read_only=True)
    service_request_location = serializers.CharField(source='service_request.location', read_only=True)
    service_request_urgency = serializers.CharField(source='service_request.urgency', read_only=True)
    
    class Meta:
        model = Task
        fields = (
            'id', 'service_request', 'service_request_description', 'service_request_location', 
            'service_request_urgency', 'assigned_to', 'status', 'notes', 'created_at'
        )
        read_only_fields = ('id', 'created_at')


class TaskDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            'id', 'service_request', 'assigned_to', 'status',
            'notes', 'proof_upload', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('service_request', 'assigned_to', 'notes')


class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('status',)
    
    def validate_status(self, value):
        # Validate status transitions
        if hasattr(self, 'instance') and self.instance:
            current_status = self.instance.status
            valid_transitions = {
                'assigned': ['in_progress'],
                'in_progress': ['completed'],
                'completed': []  # No transitions from completed
            }
            
            if value in valid_transitions.get(current_status, []):
                return value
            elif value == current_status:
                return value  # Allow same status
            else:
                raise serializers.ValidationError(
                    f'Cannot transition from {current_status} to {value}. '
                    f'Valid transitions: {valid_transitions.get(current_status, [])}'
                )
        return value


class TaskProofUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('proof_upload', 'notes')


