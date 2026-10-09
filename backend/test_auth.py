import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

import firebase_admin
from firebase_admin import auth

# Initialize firebase admin if not already initialized
try:
    from app.firebase_admin import app  # noqa: F401
except Exception as e:
    print(f"Error loading app firebase_admin: {e}")

ADMIN_EMAIL = os.environ.get("TEST_ADMIN_EMAIL", "admin@aichain.it")
# Mai hardcodare password: leggere da env. Se assente, non creare l'utente.
ADMIN_PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD")

try:
    user = auth.get_user_by_email(ADMIN_EMAIL)
    print(f"User found: {user.uid}, email: {user.email}")
except firebase_admin.auth.UserNotFoundError:
    print("User not found!")
    if not ADMIN_PASSWORD:
        print("TEST_ADMIN_PASSWORD non impostata: utente non creato.")
        sys.exit(1)
    try:
        user = auth.create_user(
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            display_name="Admin AiChain",
        )
        print(f"Created user: {user.uid}")
    except Exception as e:
        print(f"Error creating user: {e}")
except Exception as e:
    print(f"Other error: {e}")

