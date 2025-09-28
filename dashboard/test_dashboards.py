"""
Test cases for dashboard functionality.
Tests dashboard counts and data accuracy for all user roles.
"""
import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from service_requests.models import ServiceRequest
from tasks.models import Task

User = get_user_model()


class DashboardTestCase(TestCase):
    """Test cases for dashboard functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test users
        self.customer1 = User.objects.create_user(
            username='customer1',
            email='customer1@test.com',
            password='testpass123',
            role='customer',
            is_approved=True
        )
        
        self.customer2 = User.objects.create_user(
            username='customer2',
            email='customer2@test.com',
            password='testpass123',
            role='customer',
            is_approved=True
        )
        
        self.field_worker1 = User.objects.create_user(
            username='worker1',
            email='worker1@test.com',
            password='testpass123',
            role='field_worker',
            is_approved=True
        )
        
        self.field_worker2 = User.objects.create_user(
            username='worker2',
            email='worker2@test.com',
            password='testpass123',
            role='field_worker',
            is_approved=True
        )
        
        self.unapproved_worker = User.objects.create_user(
            username='unapproved_worker',
            email='unapproved@test.com',
            password='testpass123',
            role='field_worker',
            is_approved=False
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='admin',
            is_approved=True
        )
        
        # Create service requests
        self.service_request1 = ServiceRequest.objects.create(
            customer=self.customer1,
            description='Fix broken water pipe',
            location='123 Main St',
            urgency='high',
            status='open'
        )
        
        self.service_request2 = ServiceRequest.objects.create(
            customer=self.customer1,
            description='Install light fixture',
            location='456 Oak Ave',
            urgency='medium',
            status='in_progress',
            assigned_field_worker=self.field_worker1
        )
        
        self.service_request3 = ServiceRequest.objects.create(
            customer=self.customer2,
            description='Replace door handle',
            location='789 Pine St',
            urgency='low',
            status='completed',
            assigned_field_worker=self.field_worker1
        )
        
        self.service_request4 = ServiceRequest.objects.create(
            customer=self.customer2,
            description='Repair window',
            location='321 Elm St',
            urgency='high',
            status='cancelled'
        )
        
        # Create tasks
        self.task1 = Task.objects.create(
            service_request=self.service_request2,
            assigned_to=self.field_worker1,
            status='assigned'
        )
        
        self.task2 = Task.objects.create(
            service_request=self.service_request2,
            assigned_to=self.field_worker1,
            status='in_progress'
        )
        
        self.task3 = Task.objects.create(
            service_request=self.service_request3,
            assigned_to=self.field_worker1,
            status='completed'
        )
        
        self.task4 = Task.objects.create(
            service_request=self.service_request3,
            assigned_to=self.field_worker2,
            status='assigned'
        )
    
    def get_auth_headers(self, user):
        """Get authentication headers for a user."""
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}'}
    
    def test_admin_overview_dashboard(self):
        """Test admin overview dashboard returns correct counts."""
        url = reverse('dashboard:admin_overview')
        headers = self.get_auth_headers(self.admin)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user counts
        self.assertEqual(response.data['users_total'], 6)  # 2 customers + 2 workers + 1 unapproved worker + 1 admin
        self.assertEqual(response.data['users_admins'], 1)
        self.assertEqual(response.data['users_workers'], 3)  # All workers (approved + unapproved)
        self.assertEqual(response.data['users_customers'], 2)
        
        # Verify service request counts
        self.assertEqual(response.data['service_requests_total'], 4)
        self.assertEqual(response.data['service_requests_open'], 1)
        self.assertEqual(response.data['service_requests_in_progress'], 1)
        self.assertEqual(response.data['service_requests_completed'], 1)
        
        # Verify task counts
        self.assertEqual(response.data['tasks_total'], 4)
        self.assertEqual(response.data['tasks_assigned'], 2)
        self.assertEqual(response.data['tasks_in_progress'], 1)
        self.assertEqual(response.data['tasks_completed'], 1)
    
    def test_admin_overview_dashboard_unauthorized_access(self):
        """Test that non-admin users cannot access admin overview."""
        # Test with customer
        url = reverse('dashboard:admin_overview')
        headers = self.get_auth_headers(self.customer1)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test with field worker
        headers = self.get_auth_headers(self.field_worker1)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_overview_dashboard_unauthenticated_access(self):
        """Test that unauthenticated users cannot access admin overview."""
        url = reverse('dashboard:admin_overview')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_worker_summary_dashboard(self):
        """Test worker summary dashboard returns correct counts for assigned worker."""
        url = reverse('dashboard:worker_summary')
        headers = self.get_auth_headers(self.field_worker1)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify task counts for field_worker1
        self.assertEqual(response.data['assigned'], 1)  # task1
        self.assertEqual(response.data['in_progress'], 1)  # task2
        self.assertEqual(response.data['completed'], 1)  # task3
    
    def test_worker_summary_dashboard_different_worker(self):
        """Test worker summary dashboard returns correct counts for different worker."""
        url = reverse('dashboard:worker_summary')
        headers = self.get_auth_headers(self.field_worker2)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify task counts for field_worker2
        self.assertEqual(response.data['assigned'], 1)  # task4
        self.assertEqual(response.data['in_progress'], 0)
        self.assertEqual(response.data['completed'], 0)
    
    def test_worker_summary_dashboard_unauthorized_access(self):
        """Test that non-field workers cannot access worker summary."""
        # Test with customer
        url = reverse('dashboard:worker_summary')
        headers = self.get_auth_headers(self.customer1)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test with admin
        headers = self.get_auth_headers(self.admin)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_worker_summary_dashboard_unauthenticated_access(self):
        """Test that unauthenticated users cannot access worker summary."""
        url = reverse('dashboard:worker_summary')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_customer_summary_dashboard(self):
        """Test customer summary dashboard returns correct counts for customer."""
        url = reverse('dashboard:customer_summary')
        headers = self.get_auth_headers(self.customer1)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify service request counts for customer1
        self.assertEqual(response.data['requests_total'], 2)  # service_request1, service_request2
        self.assertEqual(response.data['requests_open'], 1)  # service_request1
        self.assertEqual(response.data['requests_in_progress'], 1)  # service_request2
        self.assertEqual(response.data['requests_completed'], 0)
    
    def test_customer_summary_dashboard_different_customer(self):
        """Test customer summary dashboard returns correct counts for different customer."""
        url = reverse('dashboard:customer_summary')
        headers = self.get_auth_headers(self.customer2)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify service request counts for customer2
        self.assertEqual(response.data['requests_total'], 2)  # service_request3, service_request4
        self.assertEqual(response.data['requests_open'], 0)
        self.assertEqual(response.data['requests_in_progress'], 0)
        self.assertEqual(response.data['requests_completed'], 1)  # service_request3
    
    def test_customer_summary_dashboard_unauthorized_access(self):
        """Test that non-customers cannot access customer summary."""
        # Test with field worker
        url = reverse('dashboard:customer_summary')
        headers = self.get_auth_headers(self.field_worker1)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test with admin
        headers = self.get_auth_headers(self.admin)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_customer_summary_dashboard_unauthenticated_access(self):
        """Test that unauthenticated users cannot access customer summary."""
        url = reverse('dashboard:customer_summary')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_dashboard_counts_accuracy_after_creating_new_data(self):
        """Test that dashboard counts are accurate after creating new data."""
        # Create new service request
        new_service_request = ServiceRequest.objects.create(
            customer=self.customer1,
            description='New service request',
            location='999 New St',
            urgency='medium',
            status='open'
        )
        
        # Create new task
        new_task = Task.objects.create(
            service_request=new_service_request,
            assigned_to=self.field_worker1,
            status='assigned'
        )
        
        # Test admin overview
        url = reverse('dashboard:admin_overview')
        headers = self.get_auth_headers(self.admin)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['service_requests_total'], 5)  # 4 + 1
        self.assertEqual(response.data['service_requests_open'], 2)  # 1 + 1
        self.assertEqual(response.data['tasks_total'], 5)  # 4 + 1
        self.assertEqual(response.data['tasks_assigned'], 3)  # 2 + 1
        
        # Test worker summary
        url = reverse('dashboard:worker_summary')
        headers = self.get_auth_headers(self.field_worker1)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['assigned'], 2)  # 1 + 1
        
        # Test customer summary
        url = reverse('dashboard:customer_summary')
        headers = self.get_auth_headers(self.customer1)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['requests_total'], 3)  # 2 + 1
        self.assertEqual(response.data['requests_open'], 2)  # 1 + 1
    
    def test_dashboard_counts_accuracy_after_updating_data(self):
        """Test that dashboard counts are accurate after updating data."""
        # Update service request status
        self.service_request1.status = 'in_progress'
        self.service_request1.assigned_field_worker = self.field_worker1
        self.service_request1.save()
        
        # Update task status
        self.task1.status = 'completed'
        self.task1.save()
        
        # Test admin overview
        url = reverse('dashboard:admin_overview')
        headers = self.get_auth_headers(self.admin)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['service_requests_open'], 0)  # 1 - 1
        self.assertEqual(response.data['service_requests_in_progress'], 2)  # 1 + 1
        self.assertEqual(response.data['tasks_assigned'], 1)  # 2 - 1
        self.assertEqual(response.data['tasks_completed'], 2)  # 1 + 1
        
        # Test worker summary
        url = reverse('dashboard:worker_summary')
        headers = self.get_auth_headers(self.field_worker1)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['assigned'], 0)  # 1 - 1
        self.assertEqual(response.data['completed'], 2)  # 1 + 1
    
    def test_dashboard_counts_accuracy_after_deleting_data(self):
        """Test that dashboard counts are accurate after deleting data."""
        # Delete a service request
        self.service_request4.delete()
        
        # Delete a task
        self.task4.delete()
        
        # Test admin overview
        url = reverse('dashboard:admin_overview')
        headers = self.get_auth_headers(self.admin)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['service_requests_total'], 3)  # 4 - 1
        self.assertEqual(response.data['tasks_total'], 3)  # 4 - 1
        self.assertEqual(response.data['tasks_assigned'], 1)  # 2 - 1
        
        # Test worker summary
        url = reverse('dashboard:worker_summary')
        headers = self.get_auth_headers(self.field_worker2)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['assigned'], 0)  # 1 - 1
        self.assertEqual(response.data['in_progress'], 0)
        self.assertEqual(response.data['completed'], 0)
    
    def test_dashboard_counts_with_no_data(self):
        """Test dashboard counts when there is no data."""
        # Delete all data
        ServiceRequest.objects.all().delete()
        Task.objects.all().delete()
        
        # Test admin overview
        url = reverse('dashboard:admin_overview')
        headers = self.get_auth_headers(self.admin)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['service_requests_total'], 0)
        self.assertEqual(response.data['service_requests_open'], 0)
        self.assertEqual(response.data['service_requests_in_progress'], 0)
        self.assertEqual(response.data['service_requests_completed'], 0)
        self.assertEqual(response.data['tasks_total'], 0)
        self.assertEqual(response.data['tasks_assigned'], 0)
        self.assertEqual(response.data['tasks_in_progress'], 0)
        self.assertEqual(response.data['tasks_completed'], 0)
        
        # Test worker summary
        url = reverse('dashboard:worker_summary')
        headers = self.get_auth_headers(self.field_worker1)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['assigned'], 0)
        self.assertEqual(response.data['in_progress'], 0)
        self.assertEqual(response.data['completed'], 0)
        
        # Test customer summary
        url = reverse('dashboard:customer_summary')
        headers = self.get_auth_headers(self.customer1)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['requests_total'], 0)
        self.assertEqual(response.data['requests_open'], 0)
        self.assertEqual(response.data['requests_in_progress'], 0)
        self.assertEqual(response.data['requests_completed'], 0)
    
    def test_dashboard_counts_with_mixed_statuses(self):
        """Test dashboard counts with various status combinations."""
        # Create additional data with different statuses
        ServiceRequest.objects.create(
            customer=self.customer1,
            description='Mixed status test 1',
            location='111 Test St',
            urgency='high',
            status='open'
        )
        
        ServiceRequest.objects.create(
            customer=self.customer2,
            description='Mixed status test 2',
            location='222 Test St',
            urgency='medium',
            status='in_progress',
            assigned_field_worker=self.field_worker2
        )
        
        ServiceRequest.objects.create(
            customer=self.customer1,
            description='Mixed status test 3',
            location='333 Test St',
            urgency='low',
            status='completed',
            assigned_field_worker=self.field_worker1
        )
        
        # Test admin overview
        url = reverse('dashboard:admin_overview')
        headers = self.get_auth_headers(self.admin)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify all counts are correct
        self.assertEqual(response.data['service_requests_total'], 7)  # 4 + 3
        self.assertEqual(response.data['service_requests_open'], 2)  # 1 + 1
        self.assertEqual(response.data['service_requests_in_progress'], 2)  # 1 + 1
        self.assertEqual(response.data['service_requests_completed'], 2)  # 1 + 1
        # Note: cancelled service requests are not included in the serializer
        
        # Verify user counts
        self.assertEqual(response.data['users_total'], 6)
        self.assertEqual(response.data['users_admins'], 1)
        self.assertEqual(response.data['users_workers'], 3)  # All workers
        self.assertEqual(response.data['users_customers'], 2)
    
    def test_dashboard_response_format(self):
        """Test that dashboard responses have correct format and structure."""
        # Test admin overview format
        url = reverse('dashboard:admin_overview')
        headers = self.get_auth_headers(self.admin)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        expected_keys = [
            'users_total', 'users_admins', 'users_workers', 'users_customers',
            'service_requests_total', 'service_requests_open', 'service_requests_in_progress', 
            'service_requests_completed', 'tasks_total', 'tasks_assigned', 
            'tasks_in_progress', 'tasks_completed'
        ]
        
        for key in expected_keys:
            self.assertIn(key, response.data)
            self.assertIsInstance(response.data[key], int)
        
        # Test worker summary format
        url = reverse('dashboard:worker_summary')
        headers = self.get_auth_headers(self.field_worker1)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        expected_keys = ['assigned', 'in_progress', 'completed']
        
        for key in expected_keys:
            self.assertIn(key, response.data)
            self.assertIsInstance(response.data[key], int)
        
        # Test customer summary format
        url = reverse('dashboard:customer_summary')
        headers = self.get_auth_headers(self.customer1)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        expected_keys = ['requests_total', 'requests_open', 'requests_in_progress', 'requests_completed']
        
        for key in expected_keys:
            self.assertIn(key, response.data)
            self.assertIsInstance(response.data[key], int)
