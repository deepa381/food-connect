from django.urls import path
from . import views
from . import auth_views
from . import dashboard_views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('about/', views.about, name='about'),
    path('donations/', views.donations, name='donations'),
    path('future-features/', views.future_features, name='future_features'),
    path('update-location/', views.update_location, name='update_location'),
    
    # Authentication URLs
    path('register/', auth_views.register, name='register'),
    path('login/', auth_views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Donation management URLs (legacy)
    path('donation/add/', views.donation_add, name='donation_add'),
    path('donation/<int:donation_id>/', views.donation_detail, name='donation_detail'),
    path('donation/<int:donation_id>/request-pickup/', views.donation_request_pickup, name='donation_request_pickup'),
    
    # API endpoints
    path('api/donations/', views.api_donations, name='api_donations'),
    
    # Payment URLs
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('payment/thanks/<str:payment_id>/', views.payment_thanks, name='payment_thanks'),
    
    # Legacy Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # ==================== ROLE-BASED DASHBOARDS ====================
    
    # Donor Dashboard URLs
    path('donor/', dashboard_views.donor_dashboard, name='donor_dashboard'),
    path('donor/upload/', dashboard_views.donor_upload_food, name='donor_upload_food'),
    path('donor/nutrition/', dashboard_views.donor_nutrition_analysis, name='donor_nutrition_analysis'),
    path('donor/history/', dashboard_views.donor_history, name='donor_history'),
    path('donor/nearby/', dashboard_views.donor_nearby_donations, name='donor_nearby_donations'),
    
    # NGO Dashboard URLs
    path('ngo/', dashboard_views.ngo_dashboard, name='ngo_dashboard'),
    path('ngo/calendar/', dashboard_views.ngo_calendar, name='ngo_calendar'),
    path('ngo/nutrition/', dashboard_views.ngo_nutrition_analysis, name='ngo_nutrition_analysis'),
    path('ngo/history/', dashboard_views.ngo_history, name='ngo_history'),
    path('ngo/donors/', dashboard_views.ngo_donors, name='ngo_donors'),
    path('ngo/nearby/', dashboard_views.ngo_nearby_donations, name='ngo_nearby_donations'),
    path('ngo/request-pickup/<int:donation_id>/', dashboard_views.ngo_request_pickup, name='ngo_request_pickup'),
    
    # Platform admin (custom) - moved to avoid conflict with Django admin
    path('platform-admin/', dashboard_views.admin_dashboard, name='admin_dashboard'),
    path('platform-admin/approve-ngo/<int:user_id>/', dashboard_views.admin_approve_ngo, name='admin_approve_ngo'),
    path('platform-admin/reject-ngo/<int:user_id>/', dashboard_views.admin_reject_ngo, name='admin_reject_ngo'),
    path('platform-admin/manage-users/', dashboard_views.admin_manage_users, name='admin_manage_users'),
    path('platform-admin/unapproved-ngos/', dashboard_views.admin_helper, name='admin_helper'),
]