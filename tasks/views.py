from rest_framework import viewsets, permissions, status
from rest_framework.mixins import UpdateModelMixin, DestroyModelMixin
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
from drf_yasg.utils import swagger_auto_schema


class TaskViewSet(viewsets.ReadOnlyModelViewSet, UpdateModelMixin, DestroyModelMixin):
    queryset = Task.objects.select_related('service_request', 'assigned_to').all()
    permission_classes = [permissions.IsAuthenticated & IsAdminOrAssigneeOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(operation_summary="List tasks",
                         operation_description="Get a list of tasks. Field workers see only their assigned tasks, admins see all tasks, customers see tasks for their service requests.")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Retrieve task",
                         operation_description="Get details of a specific task. Field workers can only view their assigned tasks.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


    @swagger_auto_schema(operation_summary="Update task",
                         operation_description="Update an existing task. Only admins can update tasks.")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Partially update task",
                         operation_description="Partially update an existing task. Only admins can update tasks.")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Delete task",
                         operation_description="Delete a task. Only admins can delete tasks.")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

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
        if self.action in ('update', 'partial_update'):
            return TaskCreateUpdateSerializer
        if self.action == 'set_status':
            return TaskStatusSerializer
        if self.action == 'upload_proof':
            return TaskProofUploadSerializer
        return TaskDetailSerializer


    @swagger_auto_schema(operation_summary="Update task status",
                         operation_description="Admin can set any status. Field worker can set assigned→in_progress; completion via proof upload.")
    @action(detail=True, methods=['post'], url_path='set-status')
    def set_status(self, request, pk=None):
        task = self.get_object()
        serializer = TaskStatusSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Non-admins can only move their own tasks between allowed states
        if not getattr(request.user, 'is_admin', False) and task.assigned_to_id != request.user.id:
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        # Field workers cannot directly set status to completed - they must upload proof
        if (not getattr(request.user, 'is_admin', False) and 
            serializer.validated_data.get('status') == 'completed'):
            return Response({
                'detail': 'Field workers cannot mark tasks as completed directly. Please upload proof of completion instead.'
            }, status=status.HTTP_400_BAD_REQUEST)

        old_status = task.status
        serializer.save()
        
        # Sync service request status when task is completed
        if task.status == 'completed' and old_status != 'completed':
            service_request = task.service_request
            if service_request.status != 'completed':
                service_request.status = 'completed'
                service_request.save()
        
        return Response(TaskDetailSerializer(task).data)

    @swagger_auto_schema(operation_summary="Upload proof for task",
                         operation_description="Field worker uploads file/notes. Automatically marks task and as completed.")
    @action(detail=True, methods=['post'], url_path='upload-proof')
    def upload_proof(self, request, pk=None):
        task = self.get_object()

        if not getattr(request.user, 'is_admin', False) and task.assigned_to_id != request.user.id:
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        serializer = TaskProofUploadSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        old_status = task.status
        serializer.save()
        
        # If field worker uploads proof, automatically mark task as completed
        if (not getattr(request.user, 'is_admin', False) and 
            task.status != 'completed' and 
            (task.proof_upload or task.notes)):
            task.status = 'completed'
            task.save()
            
            # Sync service request status when task is completed
            service_request = task.service_request
            if service_request.status != 'completed':
                service_request.status = 'completed'
                service_request.save()
        
        return Response(TaskDetailSerializer(task).data, status=status.HTTP_200_OK)

from django.shortcuts import render

# Create your views here.
