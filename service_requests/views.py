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
)


class ServiceRequestViewSet(viewsets.ModelViewSet):
    queryset = ServiceRequest.objects.select_related("customer").all()
    permission_classes = [permissions.IsAuthenticated & IsOwnerOrAdmin]

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
        return ServiceRequestDetailSerializer

    def perform_create(self, serializer):
        # Only customers can create service requests
        user = self.request.user
        if not getattr(user, 'is_customer', False):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only customers can create service requests.')
        serializer.save()

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

from django.shortcuts import render

# Create your views here.
