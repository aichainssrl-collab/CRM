import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

import firebase_admin
from firebase_admin import auth, credentials

# Initialize firebase admin if not already initialized
try:
    from app.firebase_admin import app
except Exception as e:
    print(f"Error loading app firebase_admin: {e}")

try:
    user = auth.get_user_by_email("admin@aichain.it")
    print(f"User found: {user.uid}, email: {user.email}")
except firebase_admin.auth.UserNotFoundError:
    print("User not found!")
    try:
        user = auth.create_user(
            email="admin@aichain.it",
            password="REMOVED_SET_TEST_ADMIN_PASSWORD_ENV",
            display_name="Admin AiChain",
        )
        print(f"Created user: {user.uid}")
    except Exception as e:
        print(f"Error creating user: {e}")
except Exception as e:
    print(f"Other error: {e}")

