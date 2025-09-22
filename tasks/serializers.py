from rest_framework import serializers
from .models import Task


class TaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            'id', 'service_request', 'assigned_to', 'status', 'created_at'
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


class TaskProofUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('proof_upload',)


