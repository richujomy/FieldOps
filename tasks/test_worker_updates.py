"""
Test cases for worker task update functionality.
Tests worker updating tasks, uploading proof, and marking tasks complete.
"""
import json
import tempfile
import os
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Task
from service_requests.models import ServiceRequest

User = get_user_model()


class WorkerTaskUpdateTestCase(TestCase):
    """Test cases for worker task update functionality."""
    
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
        
        self.other_worker = User.objects.create_user(
            username='otherworker',
            email='other@test.com',
            password='testpass123',
            role='field_worker',
            is_approved=True
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
            status='in_progress',
            assigned_field_worker=self.field_worker
        )
        
        self.service_request_other = ServiceRequest.objects.create(
            customer=self.customer,
            description='Install new light fixture',
            location='456 Oak Ave, City, State',
            urgency='medium',
            status='in_progress',
            assigned_field_worker=self.other_worker
        )
        
        # Create tasks
        self.assigned_task = Task.objects.create(
            service_request=self.service_request,
            assigned_to=self.field_worker,
            status='assigned'
        )
        
        self.in_progress_task = Task.objects.create(
            service_request=self.service_request,
            assigned_to=self.field_worker,
            status='in_progress'
        )
        
        self.completed_task = Task.objects.create(
            service_request=self.service_request,
            assigned_to=self.field_worker,
            status='completed'
        )
        
        self.other_worker_task = Task.objects.create(
            service_request=self.service_request_other,
            assigned_to=self.other_worker,
            status='assigned'
        )
    
    def get_auth_headers(self, user):
        """Get authentication headers for a user."""
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}'}
    
    def test_worker_can_view_own_tasks(self):
        """Test that field workers can view their own assigned tasks."""
        url = reverse('task-list')
        headers = self.get_auth_headers(self.field_worker)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)  # 3 tasks assigned to field_worker
        
        # Verify all tasks belong to the field worker
        task_ids = [task['id'] for task in response.data['results']]
        self.assertIn(self.assigned_task.id, task_ids)
        self.assertIn(self.in_progress_task.id, task_ids)
        self.assertIn(self.completed_task.id, task_ids)
        self.assertNotIn(self.other_worker_task.id, task_ids)
    
    def test_worker_cannot_view_other_workers_tasks(self):
        """Test that field workers cannot view other workers' tasks."""
        url = reverse('task-list')
        headers = self.get_auth_headers(self.other_worker)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only 1 task assigned to other_worker
        
        # Verify only other_worker's task is returned
        task_ids = [task['id'] for task in response.data['results']]
        self.assertIn(self.other_worker_task.id, task_ids)
        self.assertNotIn(self.assigned_task.id, task_ids)
        self.assertNotIn(self.in_progress_task.id, task_ids)
        self.assertNotIn(self.completed_task.id, task_ids)
    
    def test_worker_can_view_own_task_detail(self):
        """Test that field workers can view details of their own tasks."""
        url = reverse('task-detail', kwargs={'pk': self.assigned_task.id})
        headers = self.get_auth_headers(self.field_worker)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.assigned_task.id)
        self.assertEqual(response.data['assigned_to'], self.field_worker.id)
        self.assertEqual(response.data['status'], 'assigned')
    
    def test_worker_cannot_view_other_workers_task_detail(self):
        """Test that field workers cannot view details of other workers' tasks."""
        url = reverse('task-detail', kwargs={'pk': self.other_worker_task.id})
        headers = self.get_auth_headers(self.field_worker)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_worker_can_update_task_status_from_assigned_to_in_progress(self):
        """Test that workers can update task status from assigned to in_progress."""
        url = reverse('task-set-status', kwargs={'pk': self.assigned_task.id})
        headers = self.get_auth_headers(self.field_worker)
        
        status_data = {'status': 'in_progress'}
        
        response = self.client.post(url, data=status_data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_progress')
        
        # Verify status was updated in database
        self.assigned_task.refresh_from_db()
        self.assertEqual(self.assigned_task.status, 'in_progress')
    
    def test_worker_cannot_directly_mark_task_completed(self):
        """Test that workers cannot directly mark task as completed."""
        url = reverse('task-set-status', kwargs={'pk': self.assigned_task.id})
        headers = self.get_auth_headers(self.field_worker)
        
        status_data = {'status': 'completed'}
        
        response = self.client.post(url, data=status_data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot transition from assigned to completed', str(response.data))
    
    def test_worker_can_upload_proof_and_auto_complete_task(self):
        """Test that workers can upload proof and task is automatically marked complete."""
        url = reverse('task-upload-proof', kwargs={'pk': self.assigned_task.id})
        headers = self.get_auth_headers(self.field_worker)
        
        # Create a test file
        test_file = SimpleUploadedFile(
            "test_proof.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        proof_data = {
            'proof_upload': test_file,
            'notes': 'Task completed successfully. Photo attached as proof.'
        }
        
        response = self.client.post(url, data=proof_data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertIsNotNone(response.data['proof_upload'])
        self.assertEqual(response.data['notes'], 'Task completed successfully. Photo attached as proof.')
        
        # Verify task was updated in database
        self.assigned_task.refresh_from_db()
        self.assertEqual(self.assigned_task.status, 'completed')
        self.assertTrue(self.assigned_task.proof_upload)
        self.assertEqual(self.assigned_task.notes, 'Task completed successfully. Photo attached as proof.')
        
        # Verify service request status was updated
        self.service_request.refresh_from_db()
        self.assertEqual(self.service_request.status, 'completed')
    
    def test_worker_can_upload_proof_with_notes_only(self):
        """Test that workers can upload proof with notes only (no file)."""
        url = reverse('task-upload-proof', kwargs={'pk': self.assigned_task.id})
        headers = self.get_auth_headers(self.field_worker)
        
        proof_data = {
            'notes': 'Task completed successfully. All work done as requested.'
        }
        
        response = self.client.post(url, data=proof_data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertEqual(response.data['notes'], 'Task completed successfully. All work done as requested.')
        
        # Verify task was updated in database
        self.assigned_task.refresh_from_db()
        self.assertEqual(self.assigned_task.status, 'completed')
        self.assertEqual(self.assigned_task.notes, 'Task completed successfully. All work done as requested.')
    
    def test_worker_can_upload_proof_with_file_only(self):
        """Test that workers can upload proof with file only (no notes)."""
        url = reverse('task-upload-proof', kwargs={'pk': self.assigned_task.id})
        headers = self.get_auth_headers(self.field_worker)
        
        # Create a test file
        test_file = SimpleUploadedFile(
            "test_proof.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        proof_data = {
            'proof_upload': test_file
        }
        
        response = self.client.post(url, data=proof_data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertIsNotNone(response.data['proof_upload'])
        
        # Verify task was updated in database
        self.assigned_task.refresh_from_db()
        self.assertEqual(self.assigned_task.status, 'completed')
        self.assertTrue(self.assigned_task.proof_upload)
    
    def test_worker_cannot_upload_proof_for_other_workers_task(self):
        """Test that workers cannot upload proof for other workers' tasks."""
        url = reverse('task-upload-proof', kwargs={'pk': self.other_worker_task.id})
        headers = self.get_auth_headers(self.field_worker)
        
        # Create a test file
        test_file = SimpleUploadedFile(
            "test_proof.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        proof_data = {
            'proof_upload': test_file,
            'notes': 'Task completed successfully.'
        }
        
        response = self.client.post(url, data=proof_data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_worker_cannot_update_status_of_other_workers_task(self):
        """Test that workers cannot update status of other workers' tasks."""
        url = reverse('task-set-status', kwargs={'pk': self.other_worker_task.id})
        headers = self.get_auth_headers(self.field_worker)
        
        status_data = {'status': 'in_progress'}
        
        response = self.client.post(url, data=status_data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_worker_can_update_notes_only(self):
        """Test that workers can update notes without changing status."""
        url = reverse('task-upload-proof', kwargs={'pk': self.assigned_task.id})
        headers = self.get_auth_headers(self.field_worker)
        
        proof_data = {
            'notes': 'Updated notes: Started working on the task.'
        }
        
        response = self.client.post(url, data=proof_data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['notes'], 'Updated notes: Started working on the task.')
        # Status should be completed since notes were provided (auto-completion logic)
        self.assertEqual(response.data['status'], 'completed')
        
        # Verify task was updated in database
        self.assigned_task.refresh_from_db()
        self.assertEqual(self.assigned_task.notes, 'Updated notes: Started working on the task.')
        self.assertEqual(self.assigned_task.status, 'completed')
    
    def test_worker_can_update_in_progress_task_with_proof(self):
        """Test that workers can upload proof for in_progress tasks."""
        url = reverse('task-upload-proof', kwargs={'pk': self.in_progress_task.id})
        headers = self.get_auth_headers(self.field_worker)
        
        # Create a test file
        test_file = SimpleUploadedFile(
            "test_proof.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        proof_data = {
            'proof_upload': test_file,
            'notes': 'Task completed. Photo proof attached.'
        }
        
        response = self.client.post(url, data=proof_data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertIsNotNone(response.data['proof_upload'])
        self.assertEqual(response.data['notes'], 'Task completed. Photo proof attached.')
        
        # Verify task was updated in database
        self.in_progress_task.refresh_from_db()
        self.assertEqual(self.in_progress_task.status, 'completed')
        self.assertTrue(self.in_progress_task.proof_upload)
        self.assertEqual(self.in_progress_task.notes, 'Task completed. Photo proof attached.')
    
    def test_worker_cannot_upload_proof_for_completed_task(self):
        """Test that workers cannot upload proof for already completed tasks."""
        url = reverse('task-upload-proof', kwargs={'pk': self.completed_task.id})
        headers = self.get_auth_headers(self.field_worker)
        
        # Create a test file
        test_file = SimpleUploadedFile(
            "test_proof.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        proof_data = {
            'proof_upload': test_file,
            'notes': 'Additional proof.'
        }
        
        response = self.client.post(url, data=proof_data, **headers)
        
        # This should work but not change the status since it's already completed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
    
    def test_admin_can_update_any_task_status(self):
        """Test that admins can update any task status."""
        url = reverse('task-set-status', kwargs={'pk': self.assigned_task.id})
        headers = self.get_auth_headers(self.admin)
        
        # First transition to in_progress (valid transition)
        status_data = {'status': 'in_progress'}
        
        response = self.client.post(url, data=status_data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_progress')
        
        # Then transition to completed (valid transition)
        status_data = {'status': 'completed'}
        
        response = self.client.post(url, data=status_data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        
        # Verify task was updated in database
        self.assigned_task.refresh_from_db()
        self.assertEqual(self.assigned_task.status, 'completed')
    
    def test_admin_can_upload_proof_for_any_task(self):
        """Test that admins can upload proof for any task."""
        url = reverse('task-upload-proof', kwargs={'pk': self.other_worker_task.id})
        headers = self.get_auth_headers(self.admin)
        
        # Create a test file
        test_file = SimpleUploadedFile(
            "admin_proof.jpg",
            b"admin_file_content",
            content_type="image/jpeg"
        )
        
        proof_data = {
            'proof_upload': test_file,
            'notes': 'Admin uploaded proof for this task.'
        }
        
        response = self.client.post(url, data=proof_data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['proof_upload'])
        self.assertEqual(response.data['notes'], 'Admin uploaded proof for this task.')
    
    def test_customer_can_view_tasks_for_their_service_requests(self):
        """Test that customers can view tasks for their service requests."""
        url = reverse('task-list')
        headers = self.get_auth_headers(self.customer)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should see tasks for both service requests
        self.assertEqual(len(response.data['results']), 4)
        
        # Verify all tasks belong to customer's service requests
        task_ids = [task['id'] for task in response.data['results']]
        self.assertIn(self.assigned_task.id, task_ids)
        self.assertIn(self.in_progress_task.id, task_ids)
        self.assertIn(self.completed_task.id, task_ids)
        self.assertIn(self.other_worker_task.id, task_ids)
    
    def test_customer_can_view_task_detail_for_their_service_request(self):
        """Test that customers can view task details for their service requests."""
        url = reverse('task-detail', kwargs={'pk': self.assigned_task.id})
        headers = self.get_auth_headers(self.customer)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.assigned_task.id)
        self.assertEqual(response.data['assigned_to'], self.field_worker.id)
    
    def test_customer_cannot_update_task_status(self):
        """Test that customers cannot update task status."""
        url = reverse('task-set-status', kwargs={'pk': self.assigned_task.id})
        headers = self.get_auth_headers(self.customer)
        
        status_data = {'status': 'in_progress'}
        
        response = self.client.post(url, data=status_data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_customer_cannot_upload_proof(self):
        """Test that customers cannot upload proof."""
        url = reverse('task-upload-proof', kwargs={'pk': self.assigned_task.id})
        headers = self.get_auth_headers(self.customer)
        
        # Create a test file
        test_file = SimpleUploadedFile(
            "customer_proof.jpg",
            b"customer_file_content",
            content_type="image/jpeg"
        )
        
        proof_data = {
            'proof_upload': test_file,
            'notes': 'Customer proof.'
        }
        
        response = self.client.post(url, data=proof_data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthenticated_user_cannot_access_tasks(self):
        """Test that unauthenticated users cannot access tasks."""
        url = reverse('task-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_task_status_transition_validation(self):
        """Test that task status transitions follow proper rules."""
        # Test invalid transition from assigned to completed
        url = reverse('task-set-status', kwargs={'pk': self.assigned_task.id})
        headers = self.get_auth_headers(self.field_worker)
        
        status_data = {'status': 'completed'}
        
        response = self.client.post(url, data=status_data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot transition from assigned to completed', str(response.data))
    
    def test_upload_proof_with_invalid_file_type(self):
        """Test uploading proof with invalid file type."""
        url = reverse('task-upload-proof', kwargs={'pk': self.assigned_task.id})
        headers = self.get_auth_headers(self.field_worker)
        
        # Create a test file with invalid content type
        test_file = SimpleUploadedFile(
            "test_proof.txt",
            b"file_content",
            content_type="text/plain"
        )
        
        proof_data = {
            'proof_upload': test_file,
            'notes': 'Task completed.'
        }
        
        response = self.client.post(url, data=proof_data, **headers)
        
        # Should still work as Django doesn't validate file types by default
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
    
    def test_upload_proof_with_empty_notes_and_file(self):
        """Test uploading proof with empty notes and no file."""
        url = reverse('task-upload-proof', kwargs={'pk': self.assigned_task.id})
        headers = self.get_auth_headers(self.field_worker)
        
        proof_data = {}
        
        response = self.client.post(url, data=proof_data, **headers)
        
        # Should work but not change status since no proof was provided
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'assigned')
    
    def test_service_request_status_sync_on_task_completion(self):
        """Test that service request status is synced when task is completed."""
        # Ensure service request is in_progress
        self.service_request.status = 'in_progress'
        self.service_request.save()
        
        url = reverse('task-upload-proof', kwargs={'pk': self.assigned_task.id})
        headers = self.get_auth_headers(self.field_worker)
        
        # Create a test file
        test_file = SimpleUploadedFile(
            "test_proof.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        proof_data = {
            'proof_upload': test_file,
            'notes': 'Task completed successfully.'
        }
        
        response = self.client.post(url, data=proof_data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify service request status was updated
        self.service_request.refresh_from_db()
        self.assertEqual(self.service_request.status, 'completed')
