"""
Middleware for role-based redirects after login.
"""
from django.shortcuts import redirect
from django.urls import reverse


class RoleBasedRedirectMiddleware:
    """Middleware to redirect users to their role-specific dashboard after login."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        """
        Enforce global authentication. Allow anonymous access only to a small set
        of public paths (home, login, register, static/media if needed).

        This middleware also keeps the older role-based redirect behavior: when an
        authenticated user accesses a public landing page we redirect them to
        their role-specific dashboard.
        """
        # Normalize path
        path = request.path

        # Public allowed paths (no authentication required)
        allowed = ['/', '/home/', '/login/', '/register/']

        # Allow access to static and media files without login
        if path.startswith('/static/') or path.startswith('/media/'):
            return self.get_response(request)

        # If not authenticated and path not allowed, redirect to login
        if not request.user.is_authenticated and path not in allowed:
            return redirect('/login/')

        # Do not automatically redirect authenticated users away from public pages.
        # The application now displays a role-specific navigation bar on the
        # landing pages instead of forcing a dashboard redirect. Keep only the
        # authentication enforcement above.

        return self.get_response(request)

