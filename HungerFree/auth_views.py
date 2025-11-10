"""
Authentication views for user registration and login with role-based access.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import UserProfile, NGO, Donor
from .utils import sendEmailNotification, showInAppAlert
from decouple import config
from django.contrib.auth.models import User


def register(request):
    """User registration with role selection."""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        role = request.POST.get('role')
        
        # Validation
        if not all([username, email, password, role]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'registration/register.html')
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'registration/register.html')
        
        if role not in ['Donor', 'NGO', 'Admin']:
            messages.error(request, 'Invalid role selected.')
            return render(request, 'registration/register.html')
        
        # Check if username already exists
        from django.contrib.auth.models import User
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'registration/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'registration/register.html')
        
        # Create user
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            
            # Create user profile with role
            is_approved = True if role != 'NGO' else False  # NGOs need approval
            user_profile = UserProfile.objects.create(
                user=user,
                role=role,
                is_approved=is_approved
            )
            
            # Create role-specific profile
            if role == 'Donor':
                Donor.objects.create(
                    user=user,
                    name=username,
                    email=email
                )
            elif role == 'NGO':
                # Create NGO profile and link it to the user
                ngo = NGO.objects.create(
                    user=user,  # Link the NGO to the user
                    name=request.POST.get('ngo_name', username),
                    contact_person=request.POST.get('contact_person', username),
                    email=email,
                    phone=request.POST.get('phone', ''),
                    address=request.POST.get('address', ''),
                    city=request.POST.get('city', ''),
                    is_verified=False
                )
                # Send notification to admin
                sendEmailNotification(
                    to_email='admin@foodsaver.com',  # Replace with actual admin email
                    subject='New NGO Registration Pending Approval',
                    message=f'New NGO registration: {username} ({email}) needs approval.'
                )
                # Show notification to NGO
                showInAppAlert(
                    user=user,
                    notification_type='ngo_approval',
                    title='Registration Successful',
                    message='Your NGO account is pending approval. You will be notified once approved.'
                )
                messages.info(request, 'Your NGO account is pending approval. You will be notified once approved.')
            elif role == 'Admin':
                # Allow Admin creation only if a valid invite code is provided
                invite = request.POST.get('admin_invite_code', '')
                expected = config('ADMIN_INVITE_CODE', default='')
                if not expected or invite != expected:
                    messages.error(request, 'Invalid or missing admin invite code. Contact the site administrator.')
                    # Cleanup created objects
                    user_profile.delete()
                    user.delete()
                    return render(request, 'registration/register.html')
                # Admin account created and approved immediately
                user_profile.is_approved = True
                user_profile.save()
            
            # Auto-login after registration
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f'Registration successful! Welcome, {username}.')
                
                # Redirect based on role
                if role == 'Donor':
                    return redirect('donor_dashboard')
                elif role == 'NGO':
                    return redirect('home')  # Will be redirected after approval
                else:
                    return redirect('home')
            
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
    
    return render(request, 'registration/register.html')


def login_view(request):
    """Custom login view with role-based redirect."""
    if request.user.is_authenticated:
        # Redirect based on role
        if hasattr(request.user, 'user_profile'):
            profile = request.user.user_profile
            # Use explicit role checks and short path redirects
            try:
                if profile.role == 'Admin':
                    return redirect('/platform-admin/')
                elif profile.role == 'NGO' and profile.is_approved:
                    return redirect('/ngo/')
                elif profile.role == 'Donor':
                    return redirect('/donor/')
            except Exception:
                pass
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        selected_role = request.POST.get('role')
        
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)

            # If the login form included a role selection, ensure it matches the
            # user's actual role to avoid accidental role mismatches.
            if hasattr(user, 'user_profile'):
                profile = user.user_profile
                if selected_role and selected_role != profile.role:
                    from django.contrib.auth import logout
                    logout(request)
                    messages.error(request, 'Selected role does not match your account role.')
                    return redirect('login')

                # If NGO is not approved, inform the user but still land on home.
                if profile.role == 'NGO' and not profile.is_approved:
                    messages.warning(request, 'Your NGO account is pending approval. You will be notified once approved.')

            # Per new requirement: after login always show the Home page first.
            messages.success(request, f'Welcome back, {username}!')
            return redirect('home')
        else:
            # Provide a more actionable error message to help users debug login issues
            messages.error(request, 'Invalid username or password. Make sure your role selection matches your account and that NGO accounts are approved before logging in as NGO.')
    
    return render(request, 'registration/login.html')

