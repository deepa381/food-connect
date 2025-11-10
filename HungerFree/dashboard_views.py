"""
Dashboard views for Donor, NGO, and Admin roles.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta
from django.http import JsonResponse
from django.db.models import Q
from .models import Donation, Donor, NGO, NGOFoodRequirement, UserProfile, Notification
from django.urls import reverse
from .decorators import donor_required, ngo_required, admin_required
from .utils import matchDonationToRequirements


# ==================== DONOR DASHBOARD ====================

@donor_required
def donor_dashboard(request):
    """Donor dashboard with donation upload, nutrition analysis, and history."""
    donor = None
    if hasattr(request.user, 'donor_profile'):
        donor = request.user.donor_profile
    
    # Ensure donor object exists for authenticated users (helps keep history updated)
    if request.user.is_authenticated and not donor:
        donor = Donor.objects.filter(user=request.user).first()

    # Get donor's donations
    my_donations = Donation.objects.filter(donor=donor).order_by('-created_at')[:10] if donor else []
    # Get unread notifications (donor-specific)
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5]

    # Note: donors should NOT see or claim available donations (NGO feature).
    # Also show upcoming NGO requirements near the donor (helps donors decide what to donate)
    upcoming_requirements = []
    try:
        if donor and donor.city:
            upcoming_requirements = NGOFoodRequirement.objects.filter(ngo__city__iexact=donor.city, status='Pending', required_date__gte=date.today()).order_by('required_date')[:10]
        else:
            upcoming_requirements = NGOFoodRequirement.objects.filter(status='Pending', required_date__gte=date.today()).order_by('required_date')[:10]
    except Exception:
        upcoming_requirements = []

    # Nearby donations for donor view (available donations in donor's city or location)
    nearby_donations = []
    try:
        if donor and donor.city:
            nearby_donations = Donation.objects.filter(status='Available').filter(
                Q(donor__city__iexact=donor.city) | Q(location__icontains=donor.city)
            ).order_by('-created_at')[:20]
        else:
            nearby_donations = Donation.objects.filter(status='Available').order_by('-created_at')[:20]
    except Exception:
        nearby_donations = []

    context = {
        'donor': donor,
        'my_donations': my_donations,
        'notifications': notifications,
        'upcoming_requirements': upcoming_requirements,
        'nearby_donations': nearby_donations,
    }
    
    return render(request, 'dashboards/donor_dashboard.html', context)


@donor_required
def donor_upload_food(request):
    """Food upload form with image upload and nutrition analysis."""
    if request.method == 'POST':
        try:
            donor = None
            # Ensure authenticated users have a Donor record linked so history shows their uploads
            if request.user.is_authenticated:
                donor, _ = Donor.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'name': request.user.get_full_name() or request.user.username,
                        'email': request.user.email or ''
                    }
                )
            elif hasattr(request.user, 'donor_profile'):
                donor = request.user.donor_profile
            
            # Create donation
            donation = Donation.objects.create(
                donor=donor,
                title=request.POST.get('title'),
                description=request.POST.get('description', ''),
                quantity=int(request.POST.get('quantity', 1)),
                unit=request.POST.get('unit', 'servings'),
                location=request.POST.get('location'),
                latitude=request.POST.get('latitude') or None,
                longitude=request.POST.get('longitude') or None,
                expiry_date=request.POST.get('expiry_date'),
                status='Available',
                nutritional_info={
                    'calories': request.POST.get('calories', ''),
                    'protein': request.POST.get('protein', ''),
                    'carbs': request.POST.get('carbs', ''),
                    'fats': request.POST.get('fats', ''),
                    'notes': request.POST.get('nutrition_notes', ''),
                }
            )
            
            # Handle image upload (placeholder)
            if request.FILES.get('food_image'):
                # TODO: Save image to media storage
                # donation.image = request.FILES['food_image']
                # donation.save()
                pass
            
            # Match donation to NGO requirements
            matches = matchDonationToRequirements(donation)
            
            messages.success(request, f'Donation "{donation.title}" created successfully!')
            if matches:
                messages.info(request, f'Found {len(matches)} matching NGO requirements nearby!')
            
                return redirect('donations')
        except Exception as e:
            messages.error(request, f'Error creating donation: {str(e)}')
    
    # For GET, also show upcoming requirements so donors see what is needed while donating
    upcoming_requirements = []
    try:
        if request.user.is_authenticated:
            donor_obj = Donor.objects.filter(user=request.user).first()
            if donor_obj and donor_obj.city:
                upcoming_requirements = NGOFoodRequirement.objects.filter(ngo__city__iexact=donor_obj.city, status='Pending', required_date__gte=date.today()).order_by('required_date')[:10]
            else:
                upcoming_requirements = NGOFoodRequirement.objects.filter(status='Pending', required_date__gte=date.today()).order_by('required_date')[:10]
    except Exception:
        upcoming_requirements = []

    return render(request, 'dashboards/donor_upload_food.html', {
        'upcoming_requirements': upcoming_requirements,
    })


@donor_required
def donor_nutrition_analysis(request):
    """AI nutrition analysis for uploaded food (mock/placeholder)."""
    if request.method == 'POST':
        ingredients = request.POST.get('ingredients', '')
        meal_type = request.POST.get('meal_type', '')
        
        # Mock AI analysis (replace with actual AI call)
        from .utils import nutritional_score
        analysis = nutritional_score(ingredients, meal_type)
        
        return render(request, 'dashboards/donor_nutrition_result.html', {
            'analysis': analysis,
            'ingredients': ingredients,
        })
    
    return render(request, 'dashboards/donor_nutrition_analysis.html')


@donor_required
def donor_nearby_donations(request):
    """View nearby donations with distance info for donors."""
    donor = None
    if hasattr(request.user, 'donor_profile'):
        donor = request.user.donor_profile
    elif request.user.is_authenticated:
        donor = Donor.objects.filter(user=request.user).first()

    # Get available donations, optionally filtered by donor's city
    if donor and donor.city:
        nearby_donations = Donation.objects.filter(status='Available').filter(
            Q(donor__city__iexact=donor.city) | Q(location__icontains=donor.city)
        ).order_by('-created_at')
    else:
        nearby_donations = Donation.objects.filter(status='Available').order_by('-created_at')

    return render(request, 'dashboards/donor_nearby_donations.html', {
        'nearby_donations': nearby_donations,
        'donor': donor,
    })


@donor_required
def donor_history(request):
    """Donation history tracker for donors."""
    donor = None
    if hasattr(request.user, 'donor_profile'):
        donor = request.user.donor_profile
    else:
        # Try to resolve donor by user or email for cases where donor_profile wasn't created
        if request.user.is_authenticated:
            donor = Donor.objects.filter(user=request.user).first() or Donor.objects.filter(email=request.user.email).first()
    
    donations = Donation.objects.filter(donor=donor).order_by('-created_at') if donor else []
    
    return render(request, 'dashboards/donor_history.html', {
        'donations': donations,
    })


# ==================== NGO DASHBOARD ====================

@ngo_required
def ngo_dashboard(request):
    """NGO dashboard with calendar, nearby donations, and schedule management."""
    ngo = None
    if hasattr(request.user, 'user_profile'):
        # Get NGO associated with user
        ngo = NGO.objects.filter(email=request.user.email).first()
    
    # Get NGO's food requirements
    requirements = NGOFoodRequirement.objects.filter(ngo=ngo).order_by('required_date', 'required_time') if ngo else []
    
    # Get available donations (match by donor city or location text contains NGO city)
    if ngo and ngo.city:
        available_qs = Donation.objects.filter(status='Available').filter(
            Q(donor__city__iexact=ngo.city) | Q(location__icontains=ngo.city)
        ).order_by('-created_at')[:20]
    else:
        available_qs = Donation.objects.filter(status='Available').order_by('-created_at')[:20]

    # Build donation items with completion info (whether pickup completed)
    available_donations = []
    for d in available_qs:
        try:
            picked_completed = d.status == 'Picked Up' or d.pickup_requests.filter(status='Completed').exists()
        except Exception:
            picked_completed = False
        available_donations.append({
            'donation': d,
            'is_completed': picked_completed,
        })
    
    # Get scheduled pickups
    scheduled_pickups = []  # TODO: Get from PickupRequest model
    
    # Compute simple impact metrics for NGO: include donations explicitly assigned to this NGO
    # and donations where the NGO made pickup requests (covers cases where donation.ngo wasn't set).
    if ngo:
        received_qs = Donation.objects.filter(Q(ngo=ngo) | Q(pickup_requests__requester__email=ngo.email)).distinct().order_by('-created_at')
    else:
        received_qs = Donation.objects.none()
    total_received_servings = sum([d.quantity for d in received_qs])
    # Sum nutritional info safely
    total_calories = 0
    total_protein = 0
    for d in received_qs:
        info = d.nutritional_info or {}
        try:
            total_calories += float(info.get('calories') or 0)
        except Exception:
            pass
        try:
            total_protein += float(info.get('protein') or 0)
        except Exception:
            pass

    # Completion stats for available donations
    completed_count = sum(1 for item in available_donations if item['is_completed'])
    not_completed_count = len(available_donations) - completed_count

    # Apply optional filter from query params (all | pending)
    filter_mode = request.GET.get('filter', 'all')
    if filter_mode == 'pending':
        filtered_donations = [item for item in available_donations if not item['is_completed']]
    else:
        filtered_donations = available_donations

    nearby_donations = available_qs if available_qs is not None else Donation.objects.filter(status='Available').order_by('-created_at')[:20]

    donors_qs = Donor.objects.filter(city__iexact=ngo.city).order_by('-created_at') if ngo and ngo.city else Donor.objects.all().order_by('-created_at')[:20]

    context = {
        'ngo': ngo,
        'requirements': requirements,
        'available_donations': available_donations,
        'filtered_donations': filtered_donations,
        'filter_mode': filter_mode,
        'scheduled_pickups': scheduled_pickups,
        'donors': donors_qs,
        'donors_count': donors_qs.count() if hasattr(donors_qs, 'count') else len(donors_qs),
        'nearby_donations': nearby_donations,
        'total_received_servings': total_received_servings,
        'total_calories': total_calories,
        'total_protein': total_protein,
        'available_completed_count': completed_count,
        'available_not_completed_count': not_completed_count,
    }
    
    return render(request, 'dashboards/ngo_dashboard.html', context)


@ngo_required
def ngo_calendar(request):
    """Calendar interface for NGOs to mark food requirements."""
    ngo = None
    if hasattr(request.user, 'user_profile'):
        ngo = NGO.objects.filter(email=request.user.email).first()
    
    if request.method == 'POST':
        try:
            requirement = NGOFoodRequirement.objects.create(
                ngo=ngo,
                required_date=request.POST.get('required_date'),
                required_time=request.POST.get('required_time'),
                estimated_servings=int(request.POST.get('estimated_servings', 0)),
                description=request.POST.get('description', ''),
                status='Pending'
            )
            
            messages.success(request, f'Food requirement scheduled for {requirement.required_date} at {requirement.required_time}')
            
            # Check for nearby available donations
            nearby_donations = matchDonationToRequirements(Donation.objects.filter(status='Available').first())
            if nearby_donations:
                messages.info(request, 'Found matching donations nearby!')
            
            return redirect('ngo_calendar')
        except Exception as e:
            messages.error(request, f'Error scheduling requirement: {str(e)}')

        # Notify donors in the NGO's city about the new requirement
        try:
            from .utils import showInAppAlert, sendEmailNotification
            if ngo and ngo.city:
                donors_nearby = Donor.objects.filter(city__iexact=ngo.city)
                for donor in donors_nearby:
                    # Create in-app and email notifications
                    if donor.user:
                        showInAppAlert(
                            user=donor.user,
                            notification_type='food_shortage',
                            title='New Food Requirement Nearby',
                            message=f'An NGO in {ngo.city} has requested {requirement.estimated_servings} servings for {requirement.required_date}. Please consider donating.'
                        )
                    # Send email if donor has email
                    try:
                        sendEmailNotification(
                            to_email=donor.email,
                            subject='Food Request Near You',
                            message=f'Dear {donor.name},\n\nAn NGO in {ngo.city} has posted a food requirement for {requirement.required_date} needing {requirement.estimated_servings} servings. Visit the platform to respond.'
                        )
                    except Exception:
                        pass
        except Exception:
            # don't fail main flow on notification errors
            pass
    
    # Get all requirements for calendar view
    requirements = NGOFoodRequirement.objects.filter(ngo=ngo).order_by('required_date', 'required_time') if ngo else []
    
    return render(request, 'dashboards/ngo_calendar.html', {
        'ngo': ngo,
        'requirements': requirements,
    })


@ngo_required
def ngo_nearby_donations(request):
    """View nearby donations with map/list interface."""
    ngo = None
    if hasattr(request.user, 'user_profile'):
        ngo = NGO.objects.filter(email=request.user.email).first()
    
    # Get nearby donations (mock - would use actual location filtering)
    donations = Donation.objects.filter(status='Available').order_by('-created_at')
    
    return render(request, 'dashboards/ngo_nearby_donations.html', {
        'ngo': ngo,
        'donations': donations,
    })


@ngo_required
def ngo_nutrition_analysis(request):
    """Nutrition analysis accessible to NGOs (reuses donor analysis logic)."""
    if request.method == 'POST':
        ingredients = request.POST.get('ingredients', '')
        meal_type = request.POST.get('meal_type', '')

        from .utils import nutritional_score
        analysis = nutritional_score(ingredients, meal_type)

        return render(request, 'dashboards/donor_nutrition_result.html', {
            'analysis': analysis,
            'ingredients': ingredients,
        })

    return render(request, 'dashboards/donor_nutrition_analysis.html')


@ngo_required
def ngo_history(request):
    """Donation history for NGO: donations reserved or picked up by this NGO."""
    ngo = NGO.objects.filter(email=request.user.email).first()
    if ngo:
        # Include donations explicitly assigned to this NGO and donations requested by this NGO
        donations = Donation.objects.filter(Q(ngo=ngo) | Q(pickup_requests__requester__email=ngo.email)).distinct().order_by('-created_at')
    else:
        donations = []

    return render(request, 'dashboards/ngo_history.html', {
        'donations': donations,
    })


@ngo_required
def ngo_donors(request):
    """Simple donors list for NGOs to view potential donors."""
    # Show all donors sorted by most recent first
    donors = Donor.objects.all().order_by('-created_at')
    
    context = {
        'donors': donors,
        'total_donors': donors.count(),
    }
    
    return render(request, 'dashboards/ngo_donors.html', context)


@ngo_required
def ngo_request_pickup(request, donation_id):
    """Request pickup for a donation."""
    donation = get_object_or_404(Donation, id=donation_id)
    ngo = NGO.objects.filter(email=request.user.email).first()
    
    if request.method == 'POST':
        from .models import PickupRequest
        pickup_request = PickupRequest.objects.create(
            donation=donation,
            requester=request.user,
            requester_name=ngo.name if ngo else request.user.username,
            requester_email=ngo.email if ngo else request.user.email,
            requester_phone=ngo.phone if ngo else '',
            notes=request.POST.get('notes', ''),
            status='Pending'
        )
        # Associate donation with the NGO requesting pickup so NGO history and impact include it
        try:
            if ngo:
                donation.ngo = ngo
        except Exception:
            pass

        donation.status = 'Reserved'
        donation.save()
        # Notify the donor that their donation has been requested
        try:
            from .utils import showInAppAlert, sendEmailNotification
            if donation.donor and donation.donor.user:
                showInAppAlert(
                    user=donation.donor.user,
                    notification_type='donation_confirmed',
                    title='Your donation has a pickup request',
                    message=f'Your donation "{donation.title}" was requested by {ngo.name if ngo else request.user.username}.',
                    metadata={'donation_id': donation.id, 'pickup_request_id': pickup_request.id}
                )
                sendEmailNotification(
                    to_email=donation.donor.email,
                    subject='Donation pickup requested',
                    message=f'Dear {donation.donor.name},\n\nYour donation "{donation.title}" has been requested for pickup by {ngo.name if ngo else request.user.username}. Please check the platform for details.'
                )
        except Exception:
            pass

        messages.success(request, 'Pickup request submitted successfully!')
        return redirect('ngo_dashboard')
    
    return render(request, 'dashboards/ngo_request_pickup.html', {
        'donation': donation,
        'ngo': ngo,
    })


# ==================== ADMIN DASHBOARD ====================

@admin_required
def admin_dashboard(request):
    """Admin dashboard with platform stats, NGO approval queue, and user management."""
    # Platform stats
    total_donations = Donation.objects.count()
    total_donors = Donor.objects.count()
    total_ngos = NGO.objects.count()
    pending_ngos = UserProfile.objects.filter(role='NGO', is_approved=False, is_rejected=False).count()

    # Lists for admin management
    pending_ngo_qs = list(UserProfile.objects.filter(role='NGO', is_approved=False, is_rejected=False).select_related('user'))
    active_ngo_qs = list(UserProfile.objects.filter(role='NGO', is_approved=True, is_rejected=False).select_related('user'))
    rejected_ngo_qs = list(UserProfile.objects.filter(role='NGO', is_rejected=True).select_related('user'))

    donors_qs = list(Donor.objects.all().order_by('-created_at'))

    # Build admin change URLs for quick edit links (use Django admin namespace)
    def admin_change_url_for(obj):
        try:
            app_label = obj._meta.app_label
            model_name = obj._meta.model_name
            return reverse(f'admin:{app_label}_{model_name}_change', args=[obj.id])
        except Exception:
            return None

    pending_ngo_profiles = [{'profile': p, 'admin_url': admin_change_url_for(p)} for p in pending_ngo_qs]
    active_ngo_profiles = [{'profile': p, 'admin_url': admin_change_url_for(p)} for p in active_ngo_qs]
    rejected_ngo_profiles = [{'profile': p, 'admin_url': admin_change_url_for(p)} for p in rejected_ngo_qs]

    donors_list = [{'donor': d, 'admin_url': admin_change_url_for(d)} for d in donors_qs]

    # Recent activity
    recent_donations = Donation.objects.order_by('-created_at')[:10]

    context = {
        'total_donations': total_donations,
        'total_donors': total_donors,
        'total_ngos': total_ngos,
        'pending_ngos': pending_ngos,
        'pending_ngo_profiles': pending_ngo_profiles,
        'active_ngo_profiles': active_ngo_profiles,
        'rejected_ngo_profiles': rejected_ngo_profiles,
        'donors_list': donors_list,
        'recent_donations': recent_donations,
    }
    
    return render(request, 'dashboards/admin_dashboard.html', context)


@login_required
@donor_required
def donor_nearby_donations(request):
    """View for donors to see nearby available donations."""
    # Get the donor's city and nearby donations
    donor = request.user.donor
    donor_city = donor.city
    
    # Get all available donations in the same city
    nearby_donations = Donation.objects.filter(
        donor__city=donor_city,
        status='Available'
    ).exclude(donor=donor)  # Exclude donor's own donations
    
    return render(request, 'dashboards/donor_nearby_donations.html', {
        'nearby_donations': nearby_donations
    })


@login_required
@ngo_required
def ngo_nearby_donations(request):
    """View for NGOs to see nearby available donations."""
    # Get the NGO's city
    ngo = request.user.ngo
    ngo_city = ngo.city
    
    # Get all available donations in the same city
    nearby_donations = Donation.objects.filter(
        donor__city=ngo_city,
        status='Available'
    )
    
    return render(request, 'dashboards/ngo_nearby_donations.html', {
        'nearby_donations': nearby_donations
    })


@admin_required
def admin_approve_ngo(request, user_id):
    """Approve an NGO registration."""
    user_profile = get_object_or_404(UserProfile, user_id=user_id, role='NGO')
    
    if request.method == 'POST':
        user_profile.is_approved = True
        user_profile.save()
        
        # Send notification to NGO
        from .utils import showInAppAlert, sendEmailNotification
        showInAppAlert(
            user=user_profile.user,
            notification_type='ngo_approval',
            title='Account Approved',
            message='Your NGO account has been approved! You can now access the NGO dashboard.'
        )
        sendEmailNotification(
            to_email=user_profile.user.email,
            subject='NGO Account Approved',
            message='Your NGO account has been approved. You can now access all NGO features.'
        )
        
        messages.success(request, f'NGO account for {user_profile.user.username} has been approved.')
        return redirect('admin_dashboard')
    
    return render(request, 'dashboards/admin_approve_ngo.html', {
        'user_profile': user_profile,
    })


@admin_required
def admin_reject_ngo(request, user_id):
    """Reject an NGO registration."""
    user_profile = get_object_or_404(UserProfile, user_id=user_id, role='NGO')
    
    if request.method == 'POST':
        reason = request.POST.get('rejection_reason', '')
        
        # Send notification
        from .utils import showInAppAlert, sendEmailNotification
        showInAppAlert(
            user=user_profile.user,
            notification_type='ngo_rejection',
            title='Account Rejected',
            message=f'Your NGO account registration was rejected. Reason: {reason}'
        )
        sendEmailNotification(
            to_email=user_profile.user.email,
            subject='NGO Account Rejected',
            message=f'Your NGO account registration was rejected. Reason: {reason}'
        )

        # Soft-reject: mark the profile rejected and revoke approval
        user_profile.is_approved = False
        user_profile.is_rejected = True
        user_profile.save()

        messages.success(request, f'NGO account for {user_profile.user.username} has been rejected.')
        return redirect('admin_dashboard')
    
    return render(request, 'dashboards/admin_reject_ngo.html', {
        'user_profile': user_profile,
    })


@admin_required
def admin_manage_users(request):
    """User management interface for admins."""
    # Provide richer context: all user profiles and donors
    userprofiles = UserProfile.objects.select_related('user').order_by('-created_at')
    donors = Donor.objects.all().order_by('-created_at')

    # Also prepare convenience querysets for templates that need filtered lists
    active_ngos = UserProfile.objects.filter(role='NGO', is_approved=True).select_related('user').order_by('-created_at')
    rejected_ngos = UserProfile.objects.filter(role='NGO', is_rejected=True).select_related('user').order_by('-created_at')

    return render(request, 'dashboards/admin_manage_users.html', {
        'userprofiles': userprofiles,
        'donors': donors,
        'active_ngos': active_ngos,
        'rejected_ngos': rejected_ngos,
    })


@login_required
@donor_required
def donor_nearby_donations(request):
    """Redirect donors to the main donations page."""
    return redirect('donations')


@login_required
@ngo_required
def ngo_nearby_donations(request):
    """Redirect NGOs to the main donations page."""
    return redirect('donations')


@admin_required
def admin_helper(request):
    """Simple admin helper view: list unapproved NGO profiles and allow one-click approve."""
    pending = UserProfile.objects.filter(role='NGO', is_approved=False).select_related('user')

    if request.method == 'POST':
        # Expect a POST with 'approve_user_id' or 'reject_user_id'
        approve_id = request.POST.get('approve_user_id')
        reject_id = request.POST.get('reject_user_id')
        if approve_id:
            up = get_object_or_404(UserProfile, user_id=approve_id, role='NGO')
            up.is_approved = True
            up.save()
            messages.success(request, f'NGO {up.user.username} approved.')
            return redirect('admin_helper')
        if reject_id:
            up = get_object_or_404(UserProfile, user_id=reject_id, role='NGO')
            # Soft-reject
            up.is_approved = False
            up.is_rejected = True
            up.save()
            messages.success(request, 'NGO registration rejected (soft) and marked as rejected.')
            return redirect('admin_helper')

    return render(request, 'dashboards/admin_helper.html', {
        'pending': pending,
    })

