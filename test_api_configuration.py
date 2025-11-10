"""
Quick test to verify API keys are loaded correctly.
Run this from the FoodSaver directory: python test_api_configuration.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FoodSaver.settings')
django.setup()

from django.conf import settings
import google.generativeai as genai
import requests

def test_api_keys():
    """Test both API keys."""
    print("=" * 70)
    print("API Keys Configuration Test")
    print("=" * 70)
    
    # Test Gemini API Key
    print("\n[1] Testing Gemini API Key...")
    gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
    if gemini_key:
        print(f"   ✓ Found: {gemini_key[:15]}...{gemini_key[-5:]}")
        try:
            genai.configure(api_key=gemini_key)
            # Try the same model selection logic as views.py
            try:
                model = genai.GenerativeModel('gemini-2.0-flash')
            except:
                try:
                    model = genai.GenerativeModel('gemini-2.5-flash')
                except:
                    model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content("Say 'OK' if you can read this")
            print(f"   ✓ Test successful: {response.text.strip()[:50]}")
        except Exception as e:
            print(f"   ✗ Test failed: {str(e)}")
    else:
        print("   ✗ NOT FOUND - Check your .env file!")
    
    # Test IPStack API Key
    print("\n[2] Testing IPStack API Key...")
    ipstack_key = getattr(settings, 'IPSTACK_API_KEY', None)
    if ipstack_key:
        print(f"   ✓ Found: {ipstack_key[:15]}...{ipstack_key[-5:]}")
        try:
            url = f"http://api.ipstack.com/check?access_key={ipstack_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                print(f"   ✗ API Error: {data['error'].get('info', 'Unknown error')}")
            else:
                city = data.get('city', 'N/A')
                country = data.get('country_name', 'N/A')
                print(f"   ✓ Test successful!")
                print(f"     Location: {city}, {country}")
                print(f"     IP: {data.get('ip', 'N/A')}")
        except Exception as e:
            print(f"   ✗ Test failed: {str(e)}")
    else:
        print("   ✗ NOT FOUND - Check your .env file!")
    
    print("\n" + "=" * 70)
    
    # Summary
    if gemini_key and ipstack_key:
        print("✓ Both API keys are configured correctly!")
    else:
        print("✗ Some API keys are missing. Please check your .env file.")
    print("=" * 70)

if __name__ == "__main__":
    test_api_keys()

