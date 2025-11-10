from django.contrib import admin
from .models import Food, Donor, NGO, Donation, PickupRequest, Payment, UserProfile, NGOFoodRequirement, Notification


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'quantity', 'expiryDate', 'location']
    list_filter = ['status', 'expiryDate', 'location']
    search_fields = ['name', 'location']
    date_hierarchy = 'expiryDate'


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'city', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'city', 'created_at']
    search_fields = ['name', 'email', 'phone', 'city']
    date_hierarchy = 'created_at'


@admin.register(NGO)
class NGOAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'city', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'city', 'created_at']
    search_fields = ['name', 'contact_person', 'email', 'city', 'registration_number']
    date_hierarchy = 'created_at'


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ['title', 'donor', 'quantity', 'unit', 'location', 'expiry_date', 'status', 'created_at']
    list_filter = ['status', 'expiry_date', 'created_at', 'location']
    search_fields = ['title', 'description', 'location', 'donor__name']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'donor', 'ngo')
        }),
        ('Details', {
            'fields': ('quantity', 'unit', 'location', 'latitude', 'longitude', 'expiry_date', 'pickup_by')
        }),
        ('Status', {
            'fields': ('status', 'nutritional_info')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PickupRequest)
class PickupRequestAdmin(admin.ModelAdmin):
    list_display = ['donation', 'requester_name', 'requester_email', 'status', 'requested_at', 'scheduled_pickup']
    list_filter = ['status', 'requested_at', 'scheduled_pickup']
    search_fields = ['donation__title', 'requester_name', 'requester_email', 'requester_phone']
    date_hierarchy = 'requested_at'
    readonly_fields = ['requested_at']
    fieldsets = (
        ('Request Information', {
            'fields': ('donation', 'requester', 'requester_name', 'requester_email', 'requester_phone')
        }),
        ('Status', {
            'fields': ('status', 'scheduled_pickup', 'notes')
        }),
        ('Timestamps', {
            'fields': ('requested_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'donor', 'amount', 'gateway', 'status', 'receipt_sent', 'created_at']
    list_filter = ['status', 'gateway', 'receipt_sent', 'created_at']
    search_fields = ['payment_id', 'donor__name', 'receipt_email']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'completed_at']
    fieldsets = (
        ('Payment Information', {
            'fields': ('donor', 'amount', 'payment_id', 'gateway')
        }),
        ('Status', {
            'fields': ('status', 'receipt_sent', 'receipt_email', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'is_approved', 'created_at']
    list_filter = ['role', 'is_approved', 'created_at']
    search_fields = ['user__username', 'user__email']
    list_editable = ['is_approved']
    date_hierarchy = 'created_at'


@admin.register(NGOFoodRequirement)
class NGOFoodRequirementAdmin(admin.ModelAdmin):
    list_display = ['ngo', 'required_date', 'required_time', 'estimated_servings', 'status', 'created_at']
    list_filter = ['status', 'required_date', 'created_at']
    search_fields = ['ngo__name', 'description']
    date_hierarchy = 'required_date'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
