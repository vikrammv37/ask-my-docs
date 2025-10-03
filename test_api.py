import requests
import json

def test_endpoints():
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health endpoint: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Health endpoint error: {e}")
    
    # Test test endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/test")
        print(f"Test endpoint: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Test endpoint error: {e}")
    
    # Test upload endpoint (just to check if it accepts POST)
    try:
        response = requests.post(f"{base_url}/api/v1/documents/upload")
        print(f"Upload endpoint: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Upload endpoint error: {e}")

if __name__ == "__main__":
    test_endpoints()
