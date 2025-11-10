"""
Quick test script to verify API keys are configured correctly.
Run this with: python manage.py shell < HungerFree/test_api_keys.py
Or run: python manage.py shell
Then paste the code.
"""
from django.conf import settings
import google.generativeai as genai
import requests
from HungerFree.utils import get_ipstack_location

def test_api_keys():
    """Test both API keys."""
    print("=" * 60)
    print("Testing API Keys Configuration")
    print("=" * 60)
    
    # Test Gemini API Key
    print("\n1. Testing Gemini API Key...")
    gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
    if gemini_key:
        print(f"   ✓ Gemini API Key found: {gemini_key[:20]}...")
        try:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content("Say 'API key is working' in one word")
            print(f"   ✓ Gemini API test successful: {response.text[:50]}")
        except Exception as e:
            print(f"   ✗ Gemini API test failed: {str(e)}")
    else:
        print("   ✗ Gemini API Key not found!")
    
    # Test IPStack API Key
    print("\n2. Testing IPStack API Key...")
    ipstack_key = getattr(settings, 'IPSTACK_API_KEY', None)
    if ipstack_key:
        print(f"   ✓ IPStack API Key found: {ipstack_key[:20]}...")
        try:
            # Test IPStack API
            url = f"http://api.ipstack.com/check?access_key={ipstack_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                print(f"   ✗ IPStack API error: {data['error']['info']}")
            else:
                print(f"   ✓ IPStack API test successful!")
                print(f"     Location: {data.get('city', 'N/A')}, {data.get('country_name', 'N/A')}")
                print(f"     IP: {data.get('ip', 'N/A')}")
        except Exception as e:
            print(f"   ✗ IPStack API test failed: {str(e)}")
    else:
        print("   ✗ IPStack API Key not found!")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

# Run the test
if __name__ == "__main__":
    test_api_keys()
else:
    # When imported in Django shell
    test_api_keys()

