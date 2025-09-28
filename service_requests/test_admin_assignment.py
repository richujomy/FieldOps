"""
Test cases for admin task assignment functionality.
Tests admin assigning service requests to field workers and creating tasks.
"""
import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import ServiceRequest
from tasks.models import Task

User = get_user_model()


class AdminTaskAssignmentTestCase(TestCase):
    """Test cases for admin task assignment functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test users
        self.customer = User.objects.create_user(
            username='testcustomer',
            email='customer@test.com',
            password='testpass123',
            role='customer',
            is_approved=True
        )
        
        self.field_worker = User.objects.create_user(
            username='testworker',
            email='worker@test.com',
            password='testpass123',
            role='field_worker',
            is_approved=True
        )
        
        self.unapproved_worker = User.objects.create_user(
            username='unapprovedworker',
            email='unapproved@test.com',
            password='testpass123',
            role='field_worker',
            is_approved=False
        )
        
        self.admin = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            role='admin',
            is_approved=True
        )
        
        # Create service requests
        self.service_request = ServiceRequest.objects.create(
            customer=self.customer,
            description='Fix broken water pipe',
            location='123 Main St, City, State',
            urgency='high',
            status='open'
        )
        
        self.service_request_in_progress = ServiceRequest.objects.create(
            customer=self.customer,
            description='Install new light fixture',
            location='456 Oak Ave, City, State',
            urgency='medium',
            status='in_progress'
        )
        
        self.service_request_completed = ServiceRequest.objects.create(
            customer=self.customer,
            description='Replace door handle',
            location='789 Pine St, City, State',
            urgency='low',
            status='completed'
        )
    
    def get_auth_headers(self, user):
        """Get authentication headers for a user."""
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}'}
    
    def test_admin_can_assign_service_request_to_approved_worker(self):
        """Test that admin can assign service request to approved field worker."""
        url = reverse('service-request-assign', kwargs={'pk': self.service_request.id})
        headers = self.get_auth_headers(self.admin)
        
        assignment_data = {
            'assigned_field_worker': self.field_worker.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(assignment_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['assigned_field_worker'], self.field_worker.id)
        self.assertEqual(response.data['status'], 'in_progress')
        
        # Verify service request was updated in database
        self.service_request.refresh_from_db()
        self.assertEqual(self.service_request.assigned_field_worker, self.field_worker)
        self.assertEqual(self.service_request.status, 'in_progress')
        
        # Verify task was created
        task = Task.objects.get(service_request=self.service_request)
        self.assertEqual(task.assigned_to, self.field_worker)
        self.assertEqual(task.status, 'assigned')
    
    def test_admin_cannot_assign_to_unapproved_worker(self):
        """Test that admin cannot assign service request to unapproved field worker."""
        url = reverse('service-request-assign', kwargs={'pk': self.service_request.id})
        headers = self.get_auth_headers(self.admin)
        
        assignment_data = {
            'assigned_field_worker': self.unapproved_worker.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(assignment_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Field worker must be approved', str(response.data))
    
    def test_admin_cannot_assign_to_customer(self):
        """Test that admin cannot assign service request to customer."""
        url = reverse('service-request-assign', kwargs={'pk': self.service_request.id})
        headers = self.get_auth_headers(self.admin)
        
        assignment_data = {
            'assigned_field_worker': self.customer.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(assignment_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('User must be a field worker', str(response.data))
    
    def test_admin_cannot_assign_to_nonexistent_user(self):
        """Test that admin cannot assign service request to nonexistent user."""
        url = reverse('service-request-assign', kwargs={'pk': self.service_request.id})
        headers = self.get_auth_headers(self.admin)
        
        assignment_data = {
            'assigned_field_worker': 99999  # Nonexistent user ID
        }
        
        response = self.client.post(
            url,
            data=json.dumps(assignment_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('User does not exist', str(response.data))
    
    def test_admin_can_reassign_service_request(self):
        """Test that admin can reassign service request to different worker."""
        # First assign to one worker
        self.service_request.assigned_field_worker = self.field_worker
        self.service_request.status = 'in_progress'
        self.service_request.save()
        
        # Create another approved worker
        another_worker = User.objects.create_user(
            username='anotherworker',
            email='another@test.com',
            password='testpass123',
            role='field_worker',
            is_approved=True
        )
        
        url = reverse('service-request-assign', kwargs={'pk': self.service_request.id})
        headers = self.get_auth_headers(self.admin)
        
        assignment_data = {
            'assigned_field_worker': another_worker.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(assignment_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['assigned_field_worker'], another_worker.id)
        
        # Verify service request was updated
        self.service_request.refresh_from_db()
        self.assertEqual(self.service_request.assigned_field_worker, another_worker)
    
    def test_admin_can_unassign_service_request(self):
        """Test that admin can unassign service request (set to None)."""
        # First assign to a worker
        self.service_request.assigned_field_worker = self.field_worker
        self.service_request.status = 'in_progress'
        self.service_request.save()
        
        url = reverse('service-request-assign', kwargs={'pk': self.service_request.id})
        headers = self.get_auth_headers(self.admin)
        
        assignment_data = {
            'assigned_field_worker': None
        }
        
        response = self.client.post(
            url,
            data=json.dumps(assignment_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['assigned_field_worker'])
        
        # Verify service request was updated
        self.service_request.refresh_from_db()
        self.assertIsNone(self.service_request.assigned_field_worker)
    
    def test_customer_cannot_assign_service_request(self):
        """Test that customers cannot assign service requests."""
        url = reverse('service-request-assign', kwargs={'pk': self.service_request.id})
        headers = self.get_auth_headers(self.customer)
        
        assignment_data = {
            'assigned_field_worker': self.field_worker.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(assignment_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Only admins can assign service requests', str(response.data))
    
    def test_field_worker_cannot_assign_service_request(self):
        """Test that field workers cannot assign service requests."""
        url = reverse('service-request-assign', kwargs={'pk': self.service_request.id})
        headers = self.get_auth_headers(self.field_worker)
        
        assignment_data = {
            'assigned_field_worker': self.field_worker.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(assignment_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Only admins can assign service requests', str(response.data))
    
    def test_unauthenticated_user_cannot_assign_service_request(self):
        """Test that unauthenticated users cannot assign service requests."""
        url = reverse('service-request-assign', kwargs={'pk': self.service_request.id})
        
        assignment_data = {
            'assigned_field_worker': self.field_worker.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(assignment_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_assignment_creates_task_for_worker(self):
        """Test that assignment creates a task for the field worker."""
        url = reverse('service-request-assign', kwargs={'pk': self.service_request.id})
        headers = self.get_auth_headers(self.admin)
        
        assignment_data = {
            'assigned_field_worker': self.field_worker.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(assignment_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify task was created
        task = Task.objects.get(service_request=self.service_request)
        self.assertEqual(task.assigned_to, self.field_worker)
        self.assertEqual(task.status, 'assigned')
        self.assertEqual(task.service_request, self.service_request)
    
    def test_reassignment_creates_new_task_for_different_worker(self):
        """Test that reassignment creates new task for different worker."""
        # First assign to one worker
        self.service_request.assigned_field_worker = self.field_worker
        self.service_request.status = 'in_progress'
        self.service_request.save()
        
        # Create task
        task = Task.objects.create(
            service_request=self.service_request,
            assigned_to=self.field_worker,
            status='assigned'
        )
        
        # Create another approved worker
        another_worker = User.objects.create_user(
            username='anotherworker',
            email='another@test.com',
            password='testpass123',
            role='field_worker',
            is_approved=True
        )
        
        url = reverse('service-request-assign', kwargs={'pk': self.service_request.id})
        headers = self.get_auth_headers(self.admin)
        
        assignment_data = {
            'assigned_field_worker': another_worker.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(assignment_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify two tasks exist (one for each worker)
        tasks = Task.objects.filter(service_request=self.service_request)
        self.assertEqual(tasks.count(), 2)
        
        # Verify the new task is for the new worker
        new_task = Task.objects.get(service_request=self.service_request, assigned_to=another_worker)
        self.assertEqual(new_task.assigned_to, another_worker)
        self.assertEqual(new_task.status, 'assigned')
    
    def test_assignment_updates_service_request_status_to_in_progress(self):
        """Test that assignment updates service request status to in_progress."""
        # Ensure service request is open
        self.service_request.status = 'open'
        self.service_request.save()
        
        url = reverse('service-request-assign', kwargs={'pk': self.service_request.id})
        headers = self.get_auth_headers(self.admin)
        
        assignment_data = {
            'assigned_field_worker': self.field_worker.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(assignment_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_progress')
        
        # Verify status was updated in database
        self.service_request.refresh_from_db()
        self.assertEqual(self.service_request.status, 'in_progress')
    
    def test_assignment_does_not_change_status_if_already_in_progress(self):
        """Test that assignment doesn't change status if already in_progress."""
        # Set service request to in_progress
        self.service_request_in_progress.assigned_field_worker = self.field_worker
        self.service_request_in_progress.save()
        
        # Create another approved worker
        another_worker = User.objects.create_user(
            username='anotherworker',
            email='another@test.com',
            password='testpass123',
            role='field_worker',
            is_approved=True
        )
        
        url = reverse('service-request-assign', kwargs={'pk': self.service_request_in_progress.id})
        headers = self.get_auth_headers(self.admin)
        
        assignment_data = {
            'assigned_field_worker': another_worker.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(assignment_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_progress')
        
        # Verify status remains in_progress
        self.service_request_in_progress.refresh_from_db()
        self.assertEqual(self.service_request_in_progress.status, 'in_progress')
    
    def test_assignment_does_not_change_status_if_completed(self):
        """Test that assignment doesn't change status if already completed."""
        # Set service request to completed
        self.service_request_completed.assigned_field_worker = self.field_worker
        self.service_request_completed.save()
        
        # Create another approved worker
        another_worker = User.objects.create_user(
            username='anotherworker',
            email='another@test.com',
            password='testpass123',
            role='field_worker',
            is_approved=True
        )
        
        url = reverse('service-request-assign', kwargs={'pk': self.service_request_completed.id})
        headers = self.get_auth_headers(self.admin)
        
        assignment_data = {
            'assigned_field_worker': another_worker.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(assignment_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        
        # Verify status remains completed
        self.service_request_completed.refresh_from_db()
        self.assertEqual(self.service_request_completed.status, 'completed')
    
    def test_assignment_with_invalid_data(self):
        """Test assignment with invalid data format."""
        url = reverse('service-request-assign', kwargs={'pk': self.service_request.id})
        headers = self.get_auth_headers(self.admin)
        
        # Test with string instead of integer
        assignment_data = {
            'assigned_field_worker': 'invalid_id'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(assignment_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('assigned_field_worker', response.data)
    
    def test_assignment_with_missing_field_worker_field(self):
        """Test assignment with missing assigned_field_worker field."""
        url = reverse('service-request-assign', kwargs={'pk': self.service_request.id})
        headers = self.get_auth_headers(self.admin)
        
        assignment_data = {}  # Missing assigned_field_worker field
        
        response = self.client.post(
            url,
            data=json.dumps(assignment_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should unassign (set to None)
        self.assertIsNone(response.data['assigned_field_worker'])
    
    def test_assignment_to_nonexistent_service_request(self):
        """Test assignment to nonexistent service request."""
        url = reverse('service-request-assign', kwargs={'pk': 99999})
        headers = self.get_auth_headers(self.admin)
        
        assignment_data = {
            'assigned_field_worker': self.field_worker.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(assignment_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
