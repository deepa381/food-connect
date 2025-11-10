from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from datetime import date, timedelta
from django.db.models.signals import post_save


# User Profile with Role-Based Access Control
class UserProfile(models.Model):
    """Extended user profile with role and approval status for RBAC."""
    ROLE_CHOICES = [
        ('Donor', 'Donor'),
        ('NGO', 'NGO'),
        ('Admin', 'Admin'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Donor')
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    def is_donor(self):
        return self.role == 'Donor'
    
    def is_ngo(self):
        return self.role == 'NGO'
    
    def is_admin(self):
        return self.role == 'Admin'
    
    def can_access_dashboard(self):
        """Check if user can access their dashboard based on role and approval."""
        if self.is_admin():
            return True  # Admins always have access
        elif self.is_ngo():
            return self.is_approved  # NGOs need approval
        else:
            return True  # Donors have immediate access


# Legacy model - kept for backward compatibility
class Food(models.Model):
    name = models.CharField(max_length=200)
    status = models.CharField(choices = (('Available', 'Available'), ('Expired', 'Expired')),default='Available', max_length=100)
    quantity = models.IntegerField()
    expiryDate = models.DateField()
    location = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Donor(models.Model):
    """Represents a donor (individual or organization) who can donate food."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='donor_profile')
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class NGO(models.Model):
    """Represents an NGO that can receive donations."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='ngo_profile')
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    registration_number = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Donation(models.Model):
    """Main donation model replacing Food model with enhanced features."""
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Reserved', 'Reserved'),
        ('Picked Up', 'Picked Up'),
        ('Expired', 'Expired'),
        ('Cancelled', 'Cancelled'),
    ]
    
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='donations', null=True, blank=True)
    ngo = models.ForeignKey(NGO, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quantity = models.IntegerField()
    unit = models.CharField(max_length=50, default='servings', help_text='e.g., servings, kg, pieces')
    location = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available')
    nutritional_info = models.JSONField(default=dict, blank=True, help_text='Nutritional information as JSON')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    pickup_by = models.DateTimeField(null=True, blank=True, help_text='Preferred pickup deadline')
    
    class Meta:
        ordering = ['-created_at', 'expiry_date']
        indexes = [
            models.Index(fields=['status', 'expiry_date']),
            models.Index(fields=['location']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.quantity} {self.unit}"
    
    def is_urgent(self):
        """Check if donation expires today or tomorrow."""
        today = date.today()
        return self.expiry_date <= today + timedelta(days=1)
    
    def is_expired(self):
        """Check if donation has expired."""
        return self.expiry_date < date.today()
    
    def expire_priority(self):
        """Return priority level based on expiry date."""
        if self.is_expired():
            return 'expired'
        elif self.expiry_date == date.today():
            return 'urgent'
        elif self.expiry_date == date.today() + timedelta(days=1):
            return 'soon'
        else:
            return 'fresh'


class PickupRequest(models.Model):
    """Represents a request to pick up a donation."""
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name='pickup_requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='pickup_requests')
    requester_name = models.CharField(max_length=200)
    requester_email = models.EmailField()
    requester_phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    scheduled_pickup = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Pickup request for {self.donation.title} by {self.requester_name}"


class Payment(models.Model):
    """Represents a payment transaction for donations."""
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]
    
    GATEWAY_CHOICES = [
        ('Razorpay', 'Razorpay'),
        ('Stripe', 'Stripe'),
        ('PayU', 'PayU'),
        ('Manual', 'Manual'),
    ]
    
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.CharField(max_length=200, unique=True, help_text='Gateway transaction ID')
    gateway = models.CharField(max_length=50, choices=GATEWAY_CHOICES, default='Manual')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    receipt_sent = models.BooleanField(default=False)
    receipt_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True, help_text='Additional payment metadata')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.payment_id} - {self.amount} ({self.status})"


class NGOFoodRequirement(models.Model):
    """Represents an NGO's food requirement scheduled on their calendar."""
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Fulfilled', 'Fulfilled'),
        ('Cancelled', 'Cancelled'),
    ]
    
    ngo = models.ForeignKey(NGO, on_delete=models.CASCADE, related_name='food_requirements')
    required_date = models.DateField()
    required_time = models.TimeField()
    estimated_servings = models.IntegerField(help_text='Estimated number of servings needed')
    description = models.TextField(blank=True, help_text='Additional details about the requirement')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    fulfilled_by = models.ForeignKey(Donation, on_delete=models.SET_NULL, null=True, blank=True, related_name='fulfilled_requirements')
    
    class Meta:
        ordering = ['required_date', 'required_time']
        indexes = [
            models.Index(fields=['required_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.ngo.name} - {self.required_date} {self.required_time} ({self.estimated_servings} servings)"


class Notification(models.Model):
    """Notification system for various events."""
    TYPE_CHOICES = [
        ('ngo_approval', 'NGO Approval'),
        ('ngo_rejection', 'NGO Rejection'),
        ('food_shortage', 'Food Shortage Nearby'),
        ('donation_confirmed', 'Donation Confirmed'),
        ('donation_accepted', 'Donation Accepted'),
        ('pickup_scheduled', 'Pickup Scheduled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()}"


# Auto-create a UserProfile for superusers created with createsuperuser
@receiver(post_save, sender=User)
def ensure_user_profile_for_superuser(sender, instance, created, **kwargs):
    try:
        if created and instance.is_superuser:
            # Create UserProfile if not exists
            if not hasattr(instance, 'user_profile'):
                UserProfile.objects.create(user=instance, role='Admin', is_approved=True)
    except Exception:
        # Avoid failing saves due to signal errors
        pass


# Auto-update Donation status when a PickupRequest is completed
@receiver(post_save, sender=PickupRequest)
def mark_donation_picked_up(sender, instance, created, **kwargs):
    try:
        # If the pickup request became 'Completed', mark the related donation as Picked Up
        if instance and instance.status == 'Completed' and instance.donation:
            donation = instance.donation
            if donation.status != 'Picked Up':
                donation.status = 'Picked Up'
                donation.save()
    except Exception:
        # Do not raise from signal
        pass