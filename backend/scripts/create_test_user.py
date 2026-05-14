import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.mongodb import db

async def create_test_user_mongodb_only():
    uid = "fFW6zJBJxCYQ77y0vXskwuFQEIH3"
    email = "admin@aichain.it"
    display_name = "Admin AiChain"
    role = "admin"
    
    print(f"Sto creando il profilo CRM per {email} (UID: {uid}) nel database MongoDB...")
    
    try:
        user_data = {
            "_id": uid,
            "uid": uid,
            "email": email,
            "fullName": display_name,
            "role": role,
            "isActive": True,
        }

        # Usa upsert per creare o aggiornare
        await db.users.update_one({"_id": uid}, {"$set": user_data}, upsert=True)
        print(f"✅ Documento utente creato/aggiornato in MongoDB con successo!")
        print(f"✅ Ora puoi fare il login con {email}")

    except Exception as e:
        print(f"❌ Errore durante la creazione in MongoDB: {e}")

if __name__ == "__main__":
    asyncio.run(create_test_user_mongodb_only())