import requests
import json

API_KEY = "AIzaSY_SET_NEXT_PUBLIC_FIREBASE_API_KEY_ENV"
url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"

payload = {
    "email": "admin@aichain.it",
    "password": "REMOVED_SET_TEST_ADMIN_PASSWORD_ENV",
    "returnSecureToken": True
}

response = requests.post(url, json=payload)
print(response.status_code)
print(response.json())
