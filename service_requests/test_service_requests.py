"""
Test cases for service request functionality.
Tests customer creating service requests, viewing, updating, and rating.
"""
import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import ServiceRequest

User = get_user_model()


class ServiceRequestTestCase(TestCase):
    """Test cases for service request creation and management."""
    
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
        
        self.admin = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            role='admin',
            is_approved=True
        )
        
        # Service request data
        self.service_request_data = {
            'description': 'Fix broken water pipe in kitchen',
            'location': '123 Main St, City, State',
            'urgency': 'high'
        }
        
        self.service_request_data_medium = {
            'description': 'Install new light fixture',
            'location': '456 Oak Ave, City, State',
            'urgency': 'medium'
        }
        
        self.service_request_data_low = {
            'description': 'Replace door handle',
            'location': '789 Pine St, City, State',
            'urgency': 'low'
        }
    
    def get_auth_headers(self, user):
        """Get authentication headers for a user."""
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}'}
    
    def test_customer_create_service_request_success(self):
        """Test successful service request creation by customer."""
        url = reverse('service-request-list')
        headers = self.get_auth_headers(self.customer)
        
        response = self.client.post(
            url,
            data=json.dumps(self.service_request_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['description'], 'Fix broken water pipe in kitchen')
        self.assertEqual(response.data['location'], '123 Main St, City, State')
        self.assertEqual(response.data['urgency'], 'high')
        # Status and other fields are not returned in create response
        # They are read-only fields in the serializer
        
        # Verify service request was created in database
        # Since create serializer doesn't return id, we'll get the latest created service request
        service_request = ServiceRequest.objects.filter(customer=self.customer).latest('created_at')
        self.assertEqual(service_request.customer, self.customer)
        self.assertEqual(service_request.description, 'Fix broken water pipe in kitchen')
        self.assertEqual(service_request.location, '123 Main St, City, State')
        self.assertEqual(service_request.urgency, 'high')
        self.assertEqual(service_request.status, 'open')
    
    def test_customer_create_service_request_medium_urgency(self):
        """Test service request creation with medium urgency."""
        url = reverse('service-request-list')
        headers = self.get_auth_headers(self.customer)
        
        response = self.client.post(
            url,
            data=json.dumps(self.service_request_data_medium),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['urgency'], 'medium')
    
    def test_customer_create_service_request_low_urgency(self):
        """Test service request creation with low urgency."""
        url = reverse('service-request-list')
        headers = self.get_auth_headers(self.customer)
        
        response = self.client.post(
            url,
            data=json.dumps(self.service_request_data_low),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['urgency'], 'low')
    
    def test_customer_create_service_request_missing_description(self):
        """Test service request creation with missing description."""
        url = reverse('service-request-list')
        headers = self.get_auth_headers(self.customer)
        
        invalid_data = {
            'location': '123 Main St, City, State',
            'urgency': 'high'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(invalid_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('description', response.data)
    
    def test_customer_create_service_request_missing_location(self):
        """Test service request creation with missing location."""
        url = reverse('service-request-list')
        headers = self.get_auth_headers(self.customer)
        
        invalid_data = {
            'description': 'Fix broken water pipe',
            'urgency': 'high'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(invalid_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('location', response.data)
    
    def test_customer_create_service_request_invalid_urgency(self):
        """Test service request creation with invalid urgency."""
        url = reverse('service-request-list')
        headers = self.get_auth_headers(self.customer)
        
        invalid_data = {
            'description': 'Fix broken water pipe',
            'location': '123 Main St, City, State',
            'urgency': 'invalid_urgency'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(invalid_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('urgency', response.data)
    
    def test_field_worker_cannot_create_service_request(self):
        """Test that field workers cannot create service requests."""
        url = reverse('service-request-list')
        headers = self.get_auth_headers(self.field_worker)
        
        response = self.client.post(
            url,
            data=json.dumps(self.service_request_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Only customers can create service requests', str(response.data))
    
    def test_admin_cannot_create_service_request(self):
        """Test that admins cannot create service requests."""
        url = reverse('service-request-list')
        headers = self.get_auth_headers(self.admin)
        
        response = self.client.post(
            url,
            data=json.dumps(self.service_request_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Only customers can create service requests', str(response.data))
    
    def test_unauthenticated_user_cannot_create_service_request(self):
        """Test that unauthenticated users cannot create service requests."""
        url = reverse('service-request-list')
        
        response = self.client.post(
            url,
            data=json.dumps(self.service_request_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_customer_can_view_own_service_requests(self):
        """Test that customers can view their own service requests."""
        # Create a service request
        service_request = ServiceRequest.objects.create(
            customer=self.customer,
            description='Test service request',
            location='Test location',
            urgency='high'
        )
        
        url = reverse('service-request-list')
        headers = self.get_auth_headers(self.customer)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], service_request.id)
        self.assertEqual(response.data['results'][0]['description'], 'Test service request')
    
    def test_customer_cannot_view_other_customers_service_requests(self):
        """Test that customers cannot view other customers' service requests."""
        # Create another customer
        other_customer = User.objects.create_user(
            username='othercustomer',
            email='other@test.com',
            password='testpass123',
            role='customer',
            is_approved=True
        )
        
        # Create service request for other customer
        ServiceRequest.objects.create(
            customer=other_customer,
            description='Other customer service request',
            location='Other location',
            urgency='high'
        )
        
        url = reverse('service-request-list')
        headers = self.get_auth_headers(self.customer)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_field_worker_can_view_all_service_requests(self):
        """Test that field workers can view all service requests."""
        # Create service requests for different customers
        ServiceRequest.objects.create(
            customer=self.customer,
            description='Customer 1 service request',
            location='Location 1',
            urgency='high'
        )
        
        other_customer = User.objects.create_user(
            username='othercustomer',
            email='other@test.com',
            password='testpass123',
            role='customer',
            is_approved=True
        )
        
        ServiceRequest.objects.create(
            customer=other_customer,
            description='Customer 2 service request',
            location='Location 2',
            urgency='medium'
        )
        
        url = reverse('service-request-list')
        headers = self.get_auth_headers(self.field_worker)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_admin_can_view_all_service_requests(self):
        """Test that admins can view all service requests."""
        # Create service requests for different customers
        ServiceRequest.objects.create(
            customer=self.customer,
            description='Customer 1 service request',
            location='Location 1',
            urgency='high'
        )
        
        other_customer = User.objects.create_user(
            username='othercustomer',
            email='other@test.com',
            password='testpass123',
            role='customer',
            is_approved=True
        )
        
        ServiceRequest.objects.create(
            customer=other_customer,
            description='Customer 2 service request',
            location='Location 2',
            urgency='medium'
        )
        
        url = reverse('service-request-list')
        headers = self.get_auth_headers(self.admin)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_customer_can_view_own_service_request_detail(self):
        """Test that customers can view details of their own service requests."""
        service_request = ServiceRequest.objects.create(
            customer=self.customer,
            description='Test service request',
            location='Test location',
            urgency='high'
        )
        
        url = reverse('service-request-detail', kwargs={'pk': service_request.id})
        headers = self.get_auth_headers(self.customer)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], service_request.id)
        self.assertEqual(response.data['description'], 'Test service request')
        self.assertEqual(response.data['customer'], self.customer.id)
    
    def test_customer_cannot_view_other_customers_service_request_detail(self):
        """Test that customers cannot view details of other customers' service requests."""
        other_customer = User.objects.create_user(
            username='othercustomer',
            email='other@test.com',
            password='testpass123',
            role='customer',
            is_approved=True
        )
        
        service_request = ServiceRequest.objects.create(
            customer=other_customer,
            description='Other customer service request',
            location='Other location',
            urgency='high'
        )
        
        url = reverse('service-request-detail', kwargs={'pk': service_request.id})
        headers = self.get_auth_headers(self.customer)
        
        response = self.client.get(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_customer_can_update_own_service_request(self):
        """Test that customers can update their own service requests."""
        service_request = ServiceRequest.objects.create(
            customer=self.customer,
            description='Original description',
            location='Original location',
            urgency='high'
        )
        
        update_data = {
            'description': 'Updated description',
            'location': 'Updated location',
            'urgency': 'medium'
        }
        
        url = reverse('service-request-detail', kwargs={'pk': service_request.id})
        headers = self.get_auth_headers(self.customer)
        
        response = self.client.patch(
            url,
            data=json.dumps(update_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Updated description')
        self.assertEqual(response.data['location'], 'Updated location')
        self.assertEqual(response.data['urgency'], 'medium')
        
        # Verify changes in database
        service_request.refresh_from_db()
        self.assertEqual(service_request.description, 'Updated description')
        self.assertEqual(service_request.location, 'Updated location')
        self.assertEqual(service_request.urgency, 'medium')
    
    def test_customer_cannot_update_other_customers_service_request(self):
        """Test that customers cannot update other customers' service requests."""
        other_customer = User.objects.create_user(
            username='othercustomer',
            email='other@test.com',
            password='testpass123',
            role='customer',
            is_approved=True
        )
        
        service_request = ServiceRequest.objects.create(
            customer=other_customer,
            description='Original description',
            location='Original location',
            urgency='high'
        )
        
        update_data = {
            'description': 'Updated description',
            'location': 'Updated location',
            'urgency': 'medium'
        }
        
        url = reverse('service-request-detail', kwargs={'pk': service_request.id})
        headers = self.get_auth_headers(self.customer)
        
        response = self.client.patch(
            url,
            data=json.dumps(update_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_customer_can_rate_completed_service_request(self):
        """Test that customers can rate their completed service requests."""
        service_request = ServiceRequest.objects.create(
            customer=self.customer,
            description='Test service request',
            location='Test location',
            urgency='high',
            status='completed'
        )
        
        rating_data = {'rating': 5}
        
        url = reverse('service-request-rate', kwargs={'pk': service_request.id})
        headers = self.get_auth_headers(self.customer)
        
        response = self.client.post(
            url,
            data=json.dumps(rating_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating'], 5)
        
        # Verify rating in database
        service_request.refresh_from_db()
        self.assertEqual(service_request.rating, 5)
    
    def test_customer_cannot_rate_open_service_request(self):
        """Test that customers cannot rate open service requests."""
        service_request = ServiceRequest.objects.create(
            customer=self.customer,
            description='Test service request',
            location='Test location',
            urgency='high',
            status='open'
        )
        
        rating_data = {'rating': 5}
        
        url = reverse('service-request-rate', kwargs={'pk': service_request.id})
        headers = self.get_auth_headers(self.customer)
        
        response = self.client.post(
            url,
            data=json.dumps(rating_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Rating allowed only when status is completed', str(response.data))
    
    def test_customer_cannot_rate_other_customers_service_request(self):
        """Test that customers cannot rate other customers' service requests."""
        other_customer = User.objects.create_user(
            username='othercustomer',
            email='other@test.com',
            password='testpass123',
            role='customer',
            is_approved=True
        )
        
        service_request = ServiceRequest.objects.create(
            customer=other_customer,
            description='Other customer service request',
            location='Other location',
            urgency='high',
            status='completed'
        )
        
        rating_data = {'rating': 5}
        
        url = reverse('service-request-rate', kwargs={'pk': service_request.id})
        headers = self.get_auth_headers(self.customer)
        
        response = self.client.post(
            url,
            data=json.dumps(rating_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_invalid_rating_values(self):
        """Test rating validation with invalid values."""
        service_request = ServiceRequest.objects.create(
            customer=self.customer,
            description='Test service request',
            location='Test location',
            urgency='high',
            status='completed'
        )
        
        # Test rating too high
        rating_data = {'rating': 6}
        
        url = reverse('service-request-rate', kwargs={'pk': service_request.id})
        headers = self.get_auth_headers(self.customer)
        
        response = self.client.post(
            url,
            data=json.dumps(rating_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Rating must be between 1 and 5', str(response.data))
        
        # Test rating too low
        rating_data = {'rating': 0}
        
        response = self.client.post(
            url,
            data=json.dumps(rating_data),
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Rating must be between 1 and 5', str(response.data))
    
    def test_customer_can_delete_own_service_request(self):
        """Test that customers can delete their own service requests."""
        service_request = ServiceRequest.objects.create(
            customer=self.customer,
            description='Test service request',
            location='Test location',
            urgency='high'
        )
        
        url = reverse('service-request-detail', kwargs={'pk': service_request.id})
        headers = self.get_auth_headers(self.customer)
        
        response = self.client.delete(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify service request was deleted
        self.assertFalse(ServiceRequest.objects.filter(id=service_request.id).exists())
    
    def test_customer_cannot_delete_other_customers_service_request(self):
        """Test that customers cannot delete other customers' service requests."""
        other_customer = User.objects.create_user(
            username='othercustomer',
            email='other@test.com',
            password='testpass123',
            role='customer',
            is_approved=True
        )
        
        service_request = ServiceRequest.objects.create(
            customer=other_customer,
            description='Other customer service request',
            location='Other location',
            urgency='high'
        )
        
        url = reverse('service-request-detail', kwargs={'pk': service_request.id})
        headers = self.get_auth_headers(self.customer)
        
        response = self.client.delete(url, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify service request still exists
        self.assertTrue(ServiceRequest.objects.filter(id=service_request.id).exists())
