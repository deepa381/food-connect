"""
Role-Based Access Control (RBAC) decorators for protecting views.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def role_required(allowed_roles):
    """
    Decorator to restrict access to specific roles.
    
    Usage:
        @role_required(['Donor', 'Admin'])
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'user_profile'):
                messages.error(request, 'Please complete your profile setup.')
                return redirect('register')
            
            user_profile = request.user.user_profile
            if user_profile.role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('home')
            
            # Check if user can access dashboard (NGOs need approval)
            if not user_profile.can_access_dashboard():
                messages.warning(request, 'Your account is pending approval. Please wait for admin approval.')
                return redirect('home')
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def donor_required(view_func):
    """Decorator to restrict access to Donors only."""
    return role_required(['Donor'])(view_func)


def ngo_required(view_func):
    """Decorator to restrict access to NGOs only."""
    return role_required(['NGO'])(view_func)


def admin_required(view_func):
    """Decorator to restrict access to Admins only."""
    return role_required(['Admin'])(view_func)

