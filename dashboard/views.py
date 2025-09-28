from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from users.models import User
from service_requests.models import ServiceRequest
from tasks.models import Task

from .permissions import IsAdminUserRole
from .serializers import AdminOverviewSerializer, WorkerSummarySerializer, CustomerSummarySerializer
from drf_yasg.utils import swagger_auto_schema


@swagger_auto_schema(method='get', operation_summary="Admin overview",
                     operation_description="Admin-only: summary of users, service requests, and tasks.")
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsAdminUserRole])
def admin_overview(request):
    data = {
        'users_total': User.objects.count(),
        'users_admins': User.objects.filter(role='admin').count(),
        'users_workers': User.objects.filter(role='field_worker').count(),
        'users_customers': User.objects.filter(role='customer').count(),

        'service_requests_total': ServiceRequest.objects.count(),
        'service_requests_open': ServiceRequest.objects.filter(status='open').count(),
        'service_requests_in_progress': ServiceRequest.objects.filter(status='in_progress').count(),
        'service_requests_completed': ServiceRequest.objects.filter(status='completed').count(),

        'tasks_total': Task.objects.count(),
        'tasks_assigned': Task.objects.filter(status='assigned').count(),
        'tasks_in_progress': Task.objects.filter(status='in_progress').count(),
        'tasks_completed': Task.objects.filter(status='completed').count(),
    }

    serializer = AdminOverviewSerializer(data)
    return Response(serializer.data)



@swagger_auto_schema(method='get', operation_summary="Field worker summary",
                     operation_description="Field worker-only: counts of assigned, in-progress, and completed tasks.")
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def worker_summary(request):
    user = request.user
    if not getattr(user, 'is_field_worker', False):
        return Response({'error': 'Permission denied.'}, status=403)

    data = {
        'assigned': Task.objects.filter(assigned_to=user, status='assigned').count(),
        'in_progress': Task.objects.filter(assigned_to=user, status='in_progress').count(),
        'completed': Task.objects.filter(assigned_to=user, status='completed').count(),
    }
    serializer = WorkerSummarySerializer(data)
    return Response(serializer.data)


@swagger_auto_schema(method='get', operation_summary="Customer summary",
                     operation_description="Customer-only: counts of their service requests by status.")
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def customer_summary(request):
    user = request.user
    if not getattr(user, 'is_customer', False):
        return Response({'error': 'Permission denied.'}, status=403)

    data = {
        'requests_total': ServiceRequest.objects.filter(customer=user).count(),
        'requests_open': ServiceRequest.objects.filter(customer=user, status='open').count(),
        'requests_in_progress': ServiceRequest.objects.filter(customer=user, status='in_progress').count(),
        'requests_completed': ServiceRequest.objects.filter(customer=user, status='completed').count(),
    }
    serializer = CustomerSummarySerializer(data)
    return Response(serializer.data)

