from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import ServiceRequest
from .serializers import (
    ServiceRequestListSerializer,
    ServiceRequestDetailSerializer,
    ServiceRequestCreateUpdateSerializer,
    ServiceRequestRatingSerializer,
)


class IsOwnerOrAdmin(permissions.BasePermission):
    """Allow edits only by the request owner (customer) or admin users."""

    def has_object_permission(self, request, view, obj: ServiceRequest) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "is_admin", False):
            return True
        return obj.customer_id == user.id


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
        serializer.save()

from django.shortcuts import render

# Create your views here.
