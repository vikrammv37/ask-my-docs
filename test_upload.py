import requests

# Test the upload endpoint directly
url = "https://ask-my-docs-r1wf.onrender.com/api/v1/documents/upload"

# Create a test file
test_content = "This is a test document content."
files = {'file': ('test.txt', test_content, 'text/plain')}

try:
    response = requests.post(url, files=files)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
