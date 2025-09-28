from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ServiceRequest
from .permissions import IsOwnerOrAdmin
from .serializers import (
    ServiceRequestListSerializer,
    ServiceRequestDetailSerializer,
    ServiceRequestCreateUpdateSerializer,
    ServiceRequestRatingSerializer,
    ServiceRequestAssignmentSerializer,
)
from drf_yasg.utils import swagger_auto_schema


class ServiceRequestViewSet(viewsets.ModelViewSet):
    queryset = ServiceRequest.objects.select_related("customer").all()
    permission_classes = [permissions.IsAuthenticated & IsOwnerOrAdmin]

    @swagger_auto_schema(operation_summary="List service requests",
                         operation_description="Get a list of service requests. Customers see only their own requests, field workers and admins see all requests.")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Retrieve service request",
                         operation_description="Get details of a specific service request. Customers can only view their own requests.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Update service request",
                         operation_description="Update an existing service request. Only the owner or admin can update.")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Partially update service request",
                         operation_description="Partially update an existing service request. Only the owner or admin can update.")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Delete service request",
                         operation_description="Delete a service request. Only the owner or admin can delete.")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if getattr(user, "is_admin", False):
            return ServiceRequest.objects.all()
        if getattr(user, "is_field_worker", False):
            # Keep simple: workers can read all requests
            return ServiceRequest.objects.all()
        # Customers see only their own
        return ServiceRequest.objects.filter(customer=user)

    def get_serializer_class(self):
        if self.action in ["list"]:
            return ServiceRequestListSerializer
        if self.action in ["retrieve"]:
            return ServiceRequestDetailSerializer
        if self.action in ["create", "update", "partial_update"]:
            return ServiceRequestCreateUpdateSerializer
        if self.action == "rate":
            return ServiceRequestRatingSerializer
        if self.action == "assign":
            return ServiceRequestAssignmentSerializer
        return ServiceRequestDetailSerializer

    @swagger_auto_schema(operation_summary="Create a service request",
                         operation_description="Customer creates a new service request. Only customers can create service requests.")
    def perform_create(self, serializer):
        # Only customers can create service requests
        user = self.request.user
        if not getattr(user, 'is_customer', False):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only customers can create service requests.')
        serializer.save()

    @swagger_auto_schema(operation_summary="Rate a completed service request",
                         operation_description="Customer rates their own completed service request (1-5).")
    @action(detail=True, methods=['post'], url_path='rate')
    def rate(self, request, pk=None):
        # Customer can rate only their own request and only when completed
        service_request = self.get_object()
        user = request.user
        if not getattr(user, 'is_customer', False) or service_request.customer_id != user.id:
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
        if service_request.status != 'completed':
            return Response({'detail': 'Rating allowed only when status is completed.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ServiceRequestRatingSerializer(service_request, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ServiceRequestDetailSerializer(service_request).data)
    @swagger_auto_schema(operation_summary="Assign service request to field worker",
                         operation_description="Admin assigns a service request to a field worker. This creates a task for the field worker and updates the service request status to in_progress.")
    @action(detail=True, methods=['post'], url_path='assign')
    def assign(self, request, pk=None):
        # Only admins can assign service requests to field workers
        user = request.user
        if not getattr(user, 'is_admin', False):
            return Response({'detail': 'Only admins can assign service requests.'}, status=status.HTTP_403_FORBIDDEN)
        
        service_request = self.get_object()
        serializer = ServiceRequestAssignmentSerializer(service_request, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Handle the assignment manually since we're using IntegerField
        assigned_field_worker_id = serializer.validated_data.get('assigned_field_worker')
        if assigned_field_worker_id:
            from django.contrib.auth import get_user_model
            from tasks.models import Task
            User = get_user_model()
            try:
                field_worker = User.objects.get(id=assigned_field_worker_id)
                service_request.assigned_field_worker = field_worker
                
                # Create a task for the field worker if one doesn't exist
                task, created = Task.objects.get_or_create(
                    service_request=service_request,
                    assigned_to=field_worker,
                    defaults={'status': 'assigned'}
                )
                
            except User.DoesNotExist:
                return Response({'detail': 'Field worker not found.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            service_request.assigned_field_worker = None
        
        service_request.save()
        
        # Update status to in_progress when assigned
        if service_request.status == 'open' and assigned_field_worker_id:
            service_request.status = 'in_progress'
            service_request.save()
        
        return Response(ServiceRequestDetailSerializer(service_request).data)

from django.shortcuts import render

# Create your views here.
