"""
Test cases for user authentication functionality.
Tests user registration and login for all user roles.
"""
import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserAuthenticationTestCase(TestCase):
    """Test cases for user registration and login."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.register_url = reverse('users:register')
        self.login_url = reverse('users:login')
        
        # Test data for different user roles
        self.customer_data = {
            'username': 'testcustomer',
            'email': 'customer@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'role': 'customer',
            'phone_number': '+1234567890'
        }
        
        self.field_worker_data = {
            'username': 'testworker',
            'email': 'worker@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'role': 'field_worker',
            'phone_number': '+1234567891'
        }
        
        self.admin_data = {
            'username': 'testadmin',
            'email': 'admin@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'role': 'admin',
            'phone_number': '+1234567892'
        }
    
    def test_customer_registration_success(self):
        """Test successful customer registration."""
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.customer_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testcustomer')
        self.assertEqual(response.data['user']['role'], 'customer')
        self.assertTrue(response.data['user']['is_approved'])  # Customers are auto-approved
        
        # Verify user was created in database
        user = User.objects.get(username='testcustomer')
        self.assertEqual(user.email, 'customer@test.com')
        self.assertEqual(user.role, 'customer')
        self.assertTrue(user.check_password('testpass123'))
    
    def test_field_worker_registration_success(self):
        """Test successful field worker registration."""
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.field_worker_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testworker')
        self.assertEqual(response.data['user']['role'], 'field_worker')
        self.assertFalse(response.data['user']['is_approved'])  # Field workers need approval
        
        # Verify user was created in database
        user = User.objects.get(username='testworker')
        self.assertEqual(user.email, 'worker@test.com')
        self.assertEqual(user.role, 'field_worker')
        self.assertTrue(user.check_password('testpass123'))
    
    def test_admin_registration_success(self):
        """Test successful admin registration."""
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.admin_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testadmin')
        self.assertEqual(response.data['user']['role'], 'admin')
        
        # Verify user was created in database
        user = User.objects.get(username='testadmin')
        self.assertEqual(user.email, 'admin@test.com')
        self.assertEqual(user.role, 'admin')
        self.assertTrue(user.check_password('testpass123'))
    
    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords."""
        invalid_data = self.customer_data.copy()
        invalid_data['password_confirm'] = 'differentpassword'
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_registration_duplicate_username(self):
        """Test registration with duplicate username."""
        # Create first user
        self.client.post(
            self.register_url,
            data=json.dumps(self.customer_data),
            content_type='application/json'
        )
        
        # Try to create user with same username
        duplicate_data = self.customer_data.copy()
        duplicate_data['email'] = 'different@test.com'
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(duplicate_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
    
    def test_registration_duplicate_email(self):
        """Test registration with duplicate email (should succeed since email is not unique)."""
        # Create first user
        self.client.post(
            self.register_url,
            data=json.dumps(self.customer_data),
            content_type='application/json'
        )
        
        # Try to create user with same email (should succeed)
        duplicate_data = self.customer_data.copy()
        duplicate_data['username'] = 'differentuser'
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(duplicate_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['email'], 'customer@test.com')
    
    def test_registration_invalid_role(self):
        """Test registration with invalid role."""
        invalid_data = self.customer_data.copy()
        invalid_data['role'] = 'invalid_role'
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('role', response.data)
    
    def test_customer_login_success(self):
        """Test successful customer login."""
        # Create user first
        user = User.objects.create_user(
            username='testcustomer',
            email='customer@test.com',
            password='testpass123',
            role='customer'
        )
        
        login_data = {
            'username': 'testcustomer',
            'password': 'testpass123'
        }
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testcustomer')
        self.assertEqual(response.data['user']['role'], 'customer')
    
    def test_field_worker_login_success(self):
        """Test successful field worker login."""
        # Create user first
        user = User.objects.create_user(
            username='testworker',
            email='worker@test.com',
            password='testpass123',
            role='field_worker'
        )
        
        login_data = {
            'username': 'testworker',
            'password': 'testpass123'
        }
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testworker')
        self.assertEqual(response.data['user']['role'], 'field_worker')
    
    def test_admin_login_success(self):
        """Test successful admin login."""
        # Create user first
        user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        login_data = {
            'username': 'testadmin',
            'password': 'testpass123'
        }
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testadmin')
        self.assertEqual(response.data['user']['role'], 'admin')
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        # Create user first
        User.objects.create_user(
            username='testuser',
            email='user@test.com',
            password='testpass123',
            role='customer'
        )
        
        login_data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_login_nonexistent_user(self):
        """Test login with nonexistent user."""
        login_data = {
            'username': 'nonexistent',
            'password': 'testpass123'
        }
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_token_refresh(self):
        """Test token refresh functionality."""
        # Create user and get tokens
        user = User.objects.create_user(
            username='testuser',
            email='user@test.com',
            password='testpass123',
            role='customer'
        )
        
        refresh = RefreshToken.for_user(user)
        refresh_url = reverse('users:token_refresh')
        
        refresh_data = {
            'refresh': str(refresh)
        }
        
        response = self.client.post(
            refresh_url,
            data=json.dumps(refresh_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_user_profile_access(self):
        """Test user profile access with authentication."""
        # Create and login user
        user = User.objects.create_user(
            username='testuser',
            email='user@test.com',
            password='testpass123',
            role='customer'
        )
        
        # Get access token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        profile_url = reverse('users:profile')
        response = self.client.get(profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'user@test.com')
        self.assertEqual(response.data['role'], 'customer')
    
    def test_user_profile_access_unauthorized(self):
        """Test user profile access without authentication."""
        profile_url = reverse('users:profile')
        response = self.client.get(profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
