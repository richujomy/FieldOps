from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Task
from .serializers import (
    TaskListSerializer,
    TaskDetailSerializer,
    TaskCreateUpdateSerializer,
    TaskStatusSerializer,
    TaskProofUploadSerializer,
)
from .permissions import IsAdminOrAssigneeOrReadOnly


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.select_related('service_request', 'assigned_to').all()
    permission_classes = [permissions.IsAuthenticated & IsAdminOrAssigneeOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_admin', False):
            return self.queryset
        if getattr(user, 'is_field_worker', False):
            return self.queryset.filter(assigned_to=user)
        # customers: tasks tied to their service requests
        return self.queryset.filter(service_request__customer=user)

    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        if self.action == 'create' or self.action in ('update', 'partial_update'):
            return TaskCreateUpdateSerializer
        if self.action == 'set_status':
            return TaskStatusSerializer
        if self.action == 'upload_proof':
            return TaskProofUploadSerializer
        return TaskDetailSerializer

    # Only admins can create tasks and assign to workers
    def perform_create(self, serializer):
        if not getattr(self.request.user, 'is_admin', False):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only admins can create tasks.')
        serializer.save()

    @action(detail=True, methods=['post'], url_path='set-status')
    def set_status(self, request, pk=None):
        task = self.get_object()
        serializer = TaskStatusSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Non-admins can only move their own tasks between allowed states
        if not getattr(request.user, 'is_admin', False) and task.assigned_to_id != request.user.id:
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        old_status = task.status
        serializer.save()
        
        # Sync service request status when task is completed
        if task.status == 'completed' and old_status != 'completed':
            service_request = task.service_request
            if service_request.status != 'completed':
                service_request.status = 'completed'
                service_request.save()
        
        return Response(TaskDetailSerializer(task).data)

    @action(detail=True, methods=['post'], url_path='upload-proof')
    def upload_proof(self, request, pk=None):
        task = self.get_object()

        if not getattr(request.user, 'is_admin', False) and task.assigned_to_id != request.user.id:
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        serializer = TaskProofUploadSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TaskDetailSerializer(task).data, status=status.HTTP_200_OK)

from django.shortcuts import render

# Create your views here.
