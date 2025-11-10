from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
import google.generativeai as genai 
import requests
import re
from decouple import config
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.contrib import messages
import json
from .models import *
from datetime import date, timedelta
from django.conf import settings



# Create your views here.
def home(request):
    return render(request, 'home.html')

def chatbot(request):
    """AI chatbot view with input validation and error handling."""
    if request.method == 'POST':
        meal_type = request.POST.get('meal_type', '').strip()
        dish_name = request.POST.get('dish_name', '').strip()
        num_people = request.POST.get('num_people', '').strip()
        custom_query = request.POST.get('custom_query', '').strip()
        
        # Validate input - ensure at least one field is provided
        if not custom_query and not (dish_name and num_people):
            messages.error(request, "Please provide either a custom query or dish name with number of people.")
            return render(request, 'chatbot.html')
        
        # Basic rate limiting awareness: check session for recent requests
        # (In production, use Redis or database-based rate limiting)
        last_request = request.session.get('last_chatbot_request', 0)
        import time
        if time.time() - last_request < 2:  # 2 second cooldown
            messages.warning(request, "Please wait a moment before making another request.")
            return render(request, 'chatbot.html')
        
        request.session['last_chatbot_request'] = time.time()
        
        if custom_query:
            prompt = f''' 
            Question : I Want to Prepare {custom_query} 
            Instructions
            1. If the question is not related to food, do not answer.
            2. Provide precise amounts according to Indian Food Standards.
            3. Focus on minimizing food waste.'''
        else:
            prompt = f''' 
            Question : I Want to Prepare {dish_name} for Number of People: {num_people} for {meal_type} without wasting any Food Give me Presize Amounts of Food according to Indian Food Standards. 
            Instructions
            1. If the question is not related to food, do not answer.
            2. Provide precise amounts according to Indian Food Standards.
            3. Focus on minimizing food waste.'''
        
        try:
            response = ask_gemini(prompt)
            cleaned = clean_ai_markdown(response)
            return render(request, 'chatbot.html', context={'response': cleaned})
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, 'chatbot.html')

    return render(request, 'chatbot.html')

def ask_gemini(prompt):
    """Call Gemini API with proper error handling and rate limiting awareness."""
    api_key = getattr(settings, 'GEMINI_API_KEY', None) or config('GEMINI_API_KEY', default='')
    
    if not api_key:
        return "Error: Gemini API key not configured. Please set GEMINI_API_KEY in your environment variables."
    
    try:
        genai.configure(api_key=api_key)
        # Use the latest stable Gemini model
        # Try gemini-2.0-flash first (fastest), fallback to gemini-2.5-flash, then gemini-pro
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
        except:
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
            except:
                model = genai.GenerativeModel('gemini-pro')
        # generate_content expects a string prompt
        result = model.generate_content(prompt)
        try:
            return result.text
        except Exception:
            # Fallback formatting
            return str(result)
    except Exception as e:
        # Log error in production, return user-friendly message
        return f"Error communicating with AI service: {str(e)}. Please try again later."

def update_location(request):
    today = date.today()
    tomorrow = today + timedelta(days=1)

    def build_context(food_qs, saved_location_value):
        return {
            'current_date': today,
            'tomorrow_date': tomorrow,
            'food': food_qs,
            'saved_location': saved_location_value,
        }

    if request.method == 'POST':
        content_type = request.headers.get('Content-Type', '')
        location = None

        # Prefer JSON payload for AJAX calls
        if content_type.startswith('application/json'):
            try:
                data = json.loads(request.body.decode('utf-8') or '{}')
            except Exception:
                data = {}
            location = (data or {}).get('location')

        # Fallback to form field
        if not location:
            location = request.POST.get('location')

        if location:
            request.session['saved_location'] = location

        saved_location = request.session.get('saved_location')
        food_qs = (Food.objects.filter(location__icontains=saved_location)
                   if saved_location else Food.objects.all())

        # If AJAX/JSON request, just acknowledge and let the client reload
        is_json = content_type.startswith('application/json')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_json or is_ajax:
            return JsonResponse({'status': 'ok', 'saved_location': saved_location})

        context = build_context(food_qs, saved_location)
        context['manual_form_visible'] = True
        return render(request, 'donations.html', context)

    # GET: render with current session filter (if any)
    saved_location = request.session.get('saved_location')
    food_qs = (Food.objects.filter(location__icontains=saved_location)
               if saved_location else Food.objects.all())
    context = build_context(food_qs, saved_location)
    return render(request, 'donations.html', context)




# def get_location_data():
#     try:
#         api_key = config("IPSTACKAPIKEY")
#         url = f"http://api.ipstack.com/check?access_key={api_key}"
#         response = requests.get(url)
#         data = response.json()
#         if "error" in data:
#             return {"error": data["error"]["info"]}
#         return {
#             "ip": data.get("ip"),
#             "city": data.get("city"),
#             "region": data.get("region_name"),
#             "country": data.get("country_name"),
#             "latitude": data.get("latitude"),
#             "longitude": data.get("longitude"),
#             "zip": data.get("zip"),
#             "timezone": data.get("time_zone", {}).get("id")
#         }
#     except Exception as e:
#         return {"error": str(e)}

# # Django view that handles the URL and returns JSON response
# def detect_location(request):
#     location_data = get_location_data()
#     return render(request, 'donations.html', context={'location_data' : location_data})




def clean_ai_markdown(text: str) -> str:
    """Convert or strip simple Markdown markers so UI doesn't show raw ** and *.

    - Remove bold markers **...**
    - Convert bullet markers (* or - at line start) to a unicode bullet
    """
    if not text:
        return ""
    # Remove bold markers
    without_bold = text.replace('**', '')
    # Replace leading list markers with bullets
    bulletized = re.sub(r'^\s*[\*-]\s+', '• ', without_bold, flags=re.MULTILINE)
    return bulletized

def about(request):
    return render(request, 'about.html')

def donations(request):
    """Enhanced donations view with pagination and support for both Food and Donation models."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    saved_location = request.session.get('saved_location')
    
    # Get donations from new Donation model (preferred)
    donations_qs = Donation.objects.filter(status='Available')
    
    # Filter by location if saved
    if saved_location:
        donations_qs = donations_qs.filter(location__icontains=saved_location)
    
    # Filter by expiry priority
    expiry_filter = request.GET.get('expiry')
    if expiry_filter == 'urgent':
        donations_qs = donations_qs.filter(expiry_date=today)
    elif expiry_filter == 'soon':
        donations_qs = donations_qs.filter(expiry_date=tomorrow)
    elif expiry_filter == 'fresh':
        donations_qs = donations_qs.filter(expiry_date__gt=tomorrow)
    
    # Sorting
    sort_by = request.GET.get('sort', 'created_at')
    if sort_by == 'expiry':
        donations_qs = donations_qs.order_by('expiry_date')
    elif sort_by == 'quantity':
        donations_qs = donations_qs.order_by('-quantity')
    else:
        donations_qs = donations_qs.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(donations_qs, 12)  # 12 items per page
    page = request.GET.get('page', 1)
    try:
        donations_page = paginator.page(page)
    except:
        donations_page = paginator.page(1)
    
    # Also get legacy Food items for backward compatibility
    food_qs = (Food.objects.filter(location__icontains=saved_location)
               if saved_location else Food.objects.all())
    
    return render(request, 'donations.html', {
        'donations': donations_page,
        'food': food_qs,  # Legacy support
        'current_date': today,
        'tomorrow_date': tomorrow,
        'saved_location': saved_location,
        'expiry_filter': expiry_filter or 'all',
        'sort_by': sort_by,
    })

def future_features(request):
    return render(request, 'future.html')


# New views for donation management

def donation_add(request):
    """View to create a new donation."""
    if request.method == 'POST':
        try:
            # Get or create donor
            donor = None
            if request.user.is_authenticated:
                donor, _ = Donor.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'name': request.user.get_full_name() or request.user.username,
                        'email': request.user.email,
                    }
                )
            else:
                # Allow anonymous donations with donor info
                donor_name = request.POST.get('donor_name')
                donor_email = request.POST.get('donor_email')
                if donor_name and donor_email:
                    donor, _ = Donor.objects.get_or_create(
                        email=donor_email,
                        defaults={'name': donor_name}
                    )
            
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
            )
            
            messages.success(request, f'Donation "{donation.title}" created successfully!')
            return redirect('donation_detail', donation_id=donation.id)
        except Exception as e:
            messages.error(request, f'Error creating donation: {str(e)}')
    
    return render(request, 'donation_form.html')


def donation_detail(request, donation_id):
    """View to show donation details."""
    donation = get_object_or_404(Donation, id=donation_id)
    pickup_requests = donation.pickup_requests.filter(status__in=['Pending', 'Approved'])
    
    return render(request, 'donation_detail.html', {
        'donation': donation,
        'pickup_requests': pickup_requests,
    })


def donation_request_pickup(request, donation_id):
    """View to request pickup of a donation."""
    donation = get_object_or_404(Donation, id=donation_id)
    
    if donation.status != 'Available':
        messages.error(request, 'This donation is no longer available.')
        return redirect('donation_detail', donation_id=donation_id)
    
    if request.method == 'POST':
        try:
            pickup_request = PickupRequest.objects.create(
                donation=donation,
                requester=request.user if request.user.is_authenticated else None,
                requester_name=request.POST.get('requester_name'),
                requester_email=request.POST.get('requester_email'),
                requester_phone=request.POST.get('requester_phone'),
                notes=request.POST.get('notes', ''),
            )
            
            # Update donation status to Reserved
            donation.status = 'Reserved'
            donation.save()
            
            messages.success(request, 'Pickup request submitted successfully!')
            return redirect('donation_detail', donation_id=donation_id)
        except Exception as e:
            messages.error(request, f'Error submitting pickup request: {str(e)}')
    
    return render(request, 'pickup_request_form.html', {'donation': donation})


def api_donations(request):
    """REST API endpoint for donations listing with filters and pagination."""
    donations_qs = Donation.objects.filter(status='Available')
    
    # Filter by location
    location = request.GET.get('location')
    if location:
        donations_qs = donations_qs.filter(location__icontains=location)
    
    # Filter by expiry (urgent, soon, fresh)
    expiry_filter = request.GET.get('expiry')
    today = date.today()
    if expiry_filter == 'urgent':
        donations_qs = donations_qs.filter(expiry_date=today)
    elif expiry_filter == 'soon':
        donations_qs = donations_qs.filter(expiry_date=today + timedelta(days=1))
    elif expiry_filter == 'fresh':
        donations_qs = donations_qs.filter(expiry_date__gt=today + timedelta(days=1))
    
    # Pagination
    page = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', 10))
    paginator = Paginator(donations_qs, per_page)
    
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
    
    # Serialize donations
    donations_data = []
    for donation in page_obj:
        donations_data.append({
            'id': donation.id,
            'title': donation.title,
            'description': donation.description,
            'quantity': donation.quantity,
            'unit': donation.unit,
            'location': donation.location,
            'latitude': float(donation.latitude) if donation.latitude else None,
            'longitude': float(donation.longitude) if donation.longitude else None,
            'expiry_date': donation.expiry_date.isoformat(),
            'status': donation.status,
            'nutritional_info': donation.nutritional_info,
            'donor_name': donation.donor.name if donation.donor else None,
            'created_at': donation.created_at.isoformat(),
            'expire_priority': donation.expire_priority(),
        })
    
    return JsonResponse({
        'count': paginator.count,
        'page': page_obj.number,
        'pages': paginator.num_pages,
        'per_page': per_page,
        'results': donations_data,
    })


def payment_callback(request):
    """Handle payment gateway callback/webhook."""
    if request.method == 'POST':
        # Extract payment data from request
        payment_id = request.POST.get('payment_id') or request.GET.get('payment_id')
        status = request.POST.get('status', 'Failed')
        amount = request.POST.get('amount')
        gateway = request.POST.get('gateway', 'Manual')
        
        try:
            # Find or create payment record
            payment, created = Payment.objects.get_or_create(
                payment_id=payment_id,
                defaults={
                    'amount': amount or 0,
                    'gateway': gateway,
                    'status': status,
                }
            )
            
            if not created:
                payment.status = status
                if status == 'Completed':
                    from django.utils import timezone
                    payment.completed_at = timezone.now()
                payment.save()
            
            if status == 'Completed':
                messages.success(request, 'Payment completed successfully!')
                return redirect('payment_thanks', payment_id=payment_id)
            else:
                messages.warning(request, f'Payment status: {status}')
                return redirect('home')
        except Exception as e:
            messages.error(request, f'Error processing payment: {str(e)}')
    
    return redirect('home')


def payment_thanks(request, payment_id):
    """Thank you page after successful payment."""
    payment = get_object_or_404(Payment, payment_id=payment_id)
    return render(request, 'payment_thanks.html', {'payment': payment})


def dashboard(request):
    """Legacy dashboard view - redirects to role-based dashboards."""
    if request.user.is_authenticated:
        if hasattr(request.user, 'user_profile'):
            profile = request.user.user_profile
            if profile.is_admin():
                return redirect('admin_dashboard')
            elif profile.is_ngo() and profile.is_approved:
                return redirect('ngo_dashboard')
            elif profile.is_donor():
                return redirect('donor_dashboard')
    
    # Fallback for non-authenticated users
    context = {}
    context['recent_donations'] = Donation.objects.filter(status='Available').order_by('-created_at')[:10]
    return render(request, 'dashboard.html', context)


def logout_view(request):
    """Logout view."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')