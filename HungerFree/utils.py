"""
Utility functions for HungerFree app.
"""
import requests
from math import radians, sin, cos, sqrt, atan2
from typing import Dict, Optional, Tuple
from decouple import config
from django.conf import settings


def reverse_geocode(latitude: float, longitude: float) -> Optional[Dict[str, str]]:
    """
    Reverse geocode coordinates to get address information.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
    
    Returns:
        Dictionary with address information or None if error
    """
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        address = data.get('address', {})
        return {
            'city': address.get('city') or address.get('town') or address.get('village', ''),
            'state': address.get('state', ''),
            'country': address.get('country', ''),
            'postcode': address.get('postcode', ''),
            'full_address': data.get('display_name', ''),
        }
    except Exception as e:
        print(f"Reverse geocoding error: {e}")
        return None


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two coordinates using Haversine formula.
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
    
    Returns:
        Distance in kilometers
    """
    # Earth radius in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    
    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    distance = R * c
    return distance


def nutritional_score(ingredients: str, meal_type: str = None) -> Dict[str, any]:
    """
    Calculate a basic nutritional score based on ingredients.
    This is a placeholder - in production, integrate with a proper nutritional API.
    
    Args:
        ingredients: Comma-separated list of ingredients
        meal_type: Optional meal type (breakfast, lunch, dinner)
    
    Returns:
        Dictionary with nutritional information and score
    """
    if not ingredients:
        return {
            'score': 0,
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fats': 0,
            'fiber': 0,
            'notes': 'No ingredients provided'
        }
    
    # Simple keyword-based scoring (placeholder)
    ingredients_lower = ingredients.lower()
    
    # Basic scoring based on common healthy ingredients
    healthy_keywords = ['vegetable', 'fruit', 'whole grain', 'legume', 'nut', 'seed']
    protein_keywords = ['chicken', 'fish', 'meat', 'egg', 'dairy', 'tofu', 'bean', 'lentil']
    carb_keywords = ['rice', 'wheat', 'bread', 'pasta', 'potato', 'corn']
    
    score = 50  # Base score
    calories = 200  # Base calories
    protein = 5
    carbs = 30
    fats = 5
    fiber = 2
    
    # Adjust based on keywords
    for keyword in healthy_keywords:
        if keyword in ingredients_lower:
            score += 5
            fiber += 2
    
    for keyword in protein_keywords:
        if keyword in ingredients_lower:
            score += 3
            protein += 5
            calories += 50
    
    for keyword in carb_keywords:
        if keyword in ingredients_lower:
            carbs += 20
            calories += 80
    
    # Cap score at 100
    score = min(score, 100)
    
    return {
        'score': score,
        'calories': calories,
        'protein': round(protein, 1),
        'carbs': round(carbs, 1),
        'fats': round(fats, 1),
        'fiber': round(fiber, 1),
        'meal_type': meal_type,
        'notes': 'Basic estimation - use proper nutritional API for accurate data'
    }


def expire_priority(expiry_date, current_date=None) -> str:
    """
    Determine priority level based on expiry date.
    
    Args:
        expiry_date: Date object for expiry
        current_date: Optional current date (defaults to today)
    
    Returns:
        Priority string: 'expired', 'urgent', 'soon', or 'fresh'
    """
    from datetime import date, timedelta
    
    if current_date is None:
        current_date = date.today()
    
    if expiry_date < current_date:
        return 'expired'
    elif expiry_date == current_date:
        return 'urgent'
    elif expiry_date == current_date + timedelta(days=1):
        return 'soon'
    else:
        return 'fresh'


def get_ipstack_location(ip_address: str = None) -> Optional[Dict[str, any]]:
    """
    Get location data using ipstack API (server-side fallback).
    
    Args:
        ip_address: Optional IP address (defaults to request IP)
    
    Returns:
        Dictionary with location data or None if error
    """
    # Try to get from settings first, then fallback to config
    api_key = getattr(settings, 'IPSTACK_API_KEY', None) or config('IPSTACKAPIKEY', default='')
    if not api_key:
        return None
    
    try:
        if not ip_address:
            # Try to get IP from request (would need to pass request object)
            ip_address = 'check'  # ipstack auto-detects
        
        url = f"http://api.ipstack.com/{ip_address}?access_key={api_key}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            return {"error": data["error"]["info"]}
        
        return {
            "ip": data.get("ip"),
            "city": data.get("city"),
            "region": data.get("region_name"),
            "country": data.get("country_name"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "zip": data.get("zip"),
            "timezone": data.get("time_zone", {}).get("id")
        }
    except Exception as e:
        print(f"ipstack error: {e}")
        return None


# Notification Helper Functions
def sendEmailNotification(to_email, subject, message):
    """
    Placeholder function for sending email notifications.
    In production, integrate with email service (SendGrid, AWS SES, etc.)
    """
    # TODO: Implement actual email sending
    print(f"[EMAIL] To: {to_email}")
    print(f"[EMAIL] Subject: {subject}")
    print(f"[EMAIL] Message: {message}")
    # Example: send_mail(subject, message, 'noreply@foodsaver.com', [to_email])


def showInAppAlert(user, notification_type, title, message, metadata=None):
    """
    Create an in-app notification for the user.
    
    Args:
        user: User object
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        metadata: Optional metadata dictionary
    """
    from .models import Notification
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        metadata=metadata or {}
    )


def checkFoodShortageNearby(ngo_location, radius_km=10):
    """
    Check for food shortages (unfulfilled NGO requirements) near a location.
    This is a placeholder for the smart matching logic.
    
    Args:
        ngo_location: Location string or coordinates
        radius_km: Radius in kilometers to search
    
    Returns:
        List of nearby unfulfilled requirements
    """
    from .models import NGOFoodRequirement
    # TODO: Implement actual geographic matching
    # For now, return pending requirements
    return NGOFoodRequirement.objects.filter(status='Pending')


def matchDonationToRequirements(donation):
    """
    Match a new donation to nearby NGO requirements.
    This implements the core smart scheduling logic.
    
    Args:
        donation: Donation object
    
    Returns:
        List of matching NGOFoodRequirement objects
    """
    from .models import NGOFoodRequirement
    from .utils import distance_km
    
    # Get pending requirements
    pending_requirements = NGOFoodRequirement.objects.filter(
        status='Pending',
        required_date__gte=donation.expiry_date  # Requirement date should be before expiry
    )
    
    matches = []
    if donation.latitude and donation.longitude:
        for requirement in pending_requirements:
            if requirement.ngo.latitude and requirement.ngo.longitude:
                # Calculate distance (placeholder - would need NGO location coordinates)
                # For now, match by quantity and date
                if requirement.estimated_servings <= donation.quantity:
                    matches.append(requirement)
    
    # If we have matches, notify
    if matches:
        from django.contrib.auth.models import User
        for match in matches:
            # Try to find user associated with NGO email
            try:
                ngo_user = User.objects.get(email=match.ngo.email)
                showInAppAlert(
                    user=ngo_user,
                    notification_type='food_shortage',
                    title='Food Available Nearby',
                    message=f'Food donation matching your requirement on {match.required_date} is available!',
                    metadata={'donation_id': donation.id, 'requirement_id': match.id}
                )
            except User.DoesNotExist:
                pass  # NGO not linked to user yet
    
    return matches

