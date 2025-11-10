from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, timedelta
from .models import Donor, NGO, Donation, PickupRequest, Payment, Food
from .utils import expire_priority, distance_km, nutritional_score


class ModelTests(TestCase):
    """Test cases for models."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.donor = Donor.objects.create(
            user=self.user,
            name='Test Donor',
            email='donor@example.com',
            phone='1234567890',
            city='Mumbai'
        )
        self.ngo = NGO.objects.create(
            name='Test NGO',
            contact_person='John Doe',
            email='ngo@example.com',
            phone='9876543210',
            address='123 Main St',
            city='Mumbai'
        )
    
    def test_donor_creation(self):
        """Test Donor model creation."""
        self.assertEqual(str(self.donor), 'Test Donor')
        self.assertEqual(self.donor.email, 'donor@example.com')
        self.assertFalse(self.donor.is_verified)
    
    def test_ngo_creation(self):
        """Test NGO model creation."""
        self.assertEqual(str(self.ngo), 'Test NGO')
        self.assertEqual(self.ngo.contact_person, 'John Doe')
    
    def test_donation_creation(self):
        """Test Donation model creation."""
        donation = Donation.objects.create(
            donor=self.donor,
            title='Test Donation',
            description='Test description',
            quantity=10,
            unit='servings',
            location='Mumbai',
            expiry_date=date.today() + timedelta(days=2),
            status='Available'
        )
        self.assertEqual(str(donation), 'Test Donation - 10 servings')
        self.assertEqual(donation.status, 'Available')
        self.assertFalse(donation.is_expired())
        self.assertEqual(donation.expire_priority(), 'fresh')
    
    def test_donation_expire_priority(self):
        """Test donation expiry priority logic."""
        # Expired donation
        expired = Donation.objects.create(
            donor=self.donor,
            title='Expired Donation',
            quantity=5,
            unit='servings',
            location='Mumbai',
            expiry_date=date.today() - timedelta(days=1),
            status='Expired'
        )
        self.assertTrue(expired.is_expired())
        self.assertEqual(expired.expire_priority(), 'expired')
        
        # Urgent donation (expires today)
        urgent = Donation.objects.create(
            donor=self.donor,
            title='Urgent Donation',
            quantity=5,
            unit='servings',
            location='Mumbai',
            expiry_date=date.today(),
            status='Available'
        )
        self.assertEqual(urgent.expire_priority(), 'urgent')
        self.assertTrue(urgent.is_urgent())
        
        # Soon donation (expires tomorrow)
        soon = Donation.objects.create(
            donor=self.donor,
            title='Soon Donation',
            quantity=5,
            unit='servings',
            location='Mumbai',
            expiry_date=date.today() + timedelta(days=1),
            status='Available'
        )
        self.assertEqual(soon.expire_priority(), 'soon')
    
    def test_pickup_request_creation(self):
        """Test PickupRequest model creation."""
        donation = Donation.objects.create(
            donor=self.donor,
            title='Test Donation',
            quantity=5,
            unit='servings',
            location='Mumbai',
            expiry_date=date.today() + timedelta(days=2),
            status='Available'
        )
        pickup_request = PickupRequest.objects.create(
            donation=donation,
            requester=self.user,
            requester_name='Requester',
            requester_email='requester@example.com',
            requester_phone='1111111111',
            status='Pending'
        )
        self.assertIn('Pickup request', str(pickup_request))
        self.assertEqual(pickup_request.status, 'Pending')
    
    def test_payment_creation(self):
        """Test Payment model creation."""
        payment = Payment.objects.create(
            donor=self.donor,
            amount=100.00,
            payment_id='test_payment_123',
            gateway='Manual',
            status='Completed'
        )
        self.assertIn('Payment', str(payment))
        self.assertEqual(payment.amount, 100.00)
        self.assertEqual(payment.status, 'Completed')


class ViewTests(TestCase):
    """Test cases for views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.donor = Donor.objects.create(
            user=self.user,
            name='Test Donor',
            email='donor@example.com',
            city='Mumbai'
        )
        self.donation = Donation.objects.create(
            donor=self.donor,
            title='Test Donation',
            quantity=10,
            unit='servings',
            location='Mumbai',
            expiry_date=date.today() + timedelta(days=2),
            status='Available'
        )
    
    def test_home_view(self):
        """Test home page view."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
    
    def test_donations_view(self):
        """Test donations listing view."""
        response = self.client.get(reverse('donations'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('donations', response.context)
    
    def test_donation_detail_view(self):
        """Test donation detail view."""
        response = self.client.get(reverse('donation_detail', args=[self.donation.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['donation'], self.donation)
    
    def test_api_donations_view(self):
        """Test API donations endpoint."""
        response = self.client.get(reverse('api_donations'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertIn('results', data)
        self.assertIn('count', data)
    
    def test_api_donations_filter_by_location(self):
        """Test API donations filtering by location."""
        response = self.client.get(reverse('api_donations') + '?location=Mumbai')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(data['count'], 1)
    
    def test_donation_add_view_get(self):
        """Test donation add form GET request."""
        response = self.client.get(reverse('donation_add'))
        self.assertEqual(response.status_code, 200)
    
    def test_donation_add_view_post(self):
        """Test donation add form POST request."""
        self.client.login(username='testuser', password='testpass123')
        data = {
            'title': 'New Donation',
            'description': 'Test description',
            'quantity': 5,
            'unit': 'servings',
            'location': 'Delhi',
            'expiry_date': date.today() + timedelta(days=3),
        }
        response = self.client.post(reverse('donation_add'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertTrue(Donation.objects.filter(title='New Donation').exists())


class UtilsTests(TestCase):
    """Test cases for utility functions."""
    
    def test_expire_priority(self):
        """Test expire_priority utility function."""
        today = date.today()
        self.assertEqual(expire_priority(today - timedelta(days=1)), 'expired')
        self.assertEqual(expire_priority(today), 'urgent')
        self.assertEqual(expire_priority(today + timedelta(days=1)), 'soon')
        self.assertEqual(expire_priority(today + timedelta(days=2)), 'fresh')
    
    def test_distance_km(self):
        """Test distance calculation."""
        # Distance between Mumbai and Delhi (approximately 1400 km)
        mumbai_lat, mumbai_lon = 19.0760, 72.8777
        delhi_lat, delhi_lon = 28.6139, 77.2090
        distance = distance_km(mumbai_lat, mumbai_lon, delhi_lat, delhi_lon)
        self.assertGreater(distance, 1000)  # Should be more than 1000 km
        self.assertLess(distance, 2000)  # Should be less than 2000 km
    
    def test_nutritional_score(self):
        """Test nutritional score calculation."""
        result = nutritional_score('vegetable, fruit, chicken')
        self.assertIn('score', result)
        self.assertIn('calories', result)
        self.assertIn('protein', result)
        self.assertGreater(result['score'], 0)
        self.assertLessEqual(result['score'], 100)
    
    def test_nutritional_score_empty(self):
        """Test nutritional score with empty input."""
        result = nutritional_score('')
        self.assertEqual(result['score'], 0)
        self.assertEqual(result['calories'], 0)
