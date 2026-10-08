#!/usr/bin/env python3
"""
Script di migrazione dati: MongoDB Locale → Firestore Cloud

Uso:
    # Dry-run (verifica senza scrivere)
    python migrate_to_firestore.py --dry-run
    
    # Migrazione completa
    python migrate_to_firestore.py
    
    # Solo una collection
    python migrate_to_firestore.py --collection=leads

Requisiti:
    pip install motor google-cloud-firestore
"""

import argparse
import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List

from motor.motor_asyncio import AsyncIOMotorClient
from google.cloud import firestore


MONGODB_URI = "mongodb://localhost:27017"
MONGODB_DB = "crm-aichain-db"
FIRESTORE_PROJECT = "level-facility-479122-u4"
FIRESTORE_DATABASE = "(default)"

COLLECTIONS = ["users", "leads", "deals", "activities", "tasks"]


def convert_mongo_to_firestore(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Converti documento MongoDB in formato Firestore."""
    if doc is None:
        return None
    
    result = dict(doc)
    
    if "_id" in result:
        result["id"] = str(result.pop("_id"))
    
    for key, value in list(result.items()):
        if isinstance(value, datetime):
            result[key] = firestore.SERVER_TIMESTAMP
        elif isinstance(value, list):
            result[key] = [convert_mongo_to_firestore(v) if isinstance(v, dict) else v for v in value]
        elif isinstance(value, dict):
            result[key] = convert_mongo_to_firestore(value)
    
    return result


async def fetch_mongo_documents(mongo_client: AsyncIOMotorClient, collection: str) -> List[Dict]:
    """Estrai tutti i documenti da una collection MongoDB."""
    db = mongo_client[MONGODB_DB]
    cursor = db[collection].find({})
    docs = await cursor.to_list(length=None)
    return docs


async def migrate_collection_async(
    mongo_client: AsyncIOMotorClient,
    firestore_db: firestore.Client,
    collection: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Migra una collection da MongoDB a Firestore (async)."""
    print(f"\n📦 Migrazione collection: {collection}")
    
    docs = await fetch_mongo_documents(mongo_client, collection)
    print(f"   Trovati {len(docs)} documenti")
    
    if dry_run:
        print(f"   [DRY-RUN] Primi 3 documenti:")
        for doc in docs[:3]:
            converted = convert_mongo_to_firestore(doc)
            print(f"   - {json.dumps(converted, default=str, indent=4)[:200]}...")
        return {"migrated": 0, "skipped": len(docs)}
    
    batch = firestore_db.batch()
    count = 0
    errors = 0
    
    for doc in docs:
        try:
            converted = convert_mongo_to_firestore(doc)
            doc_id = converted.pop("id")
            doc_ref = firestore_db.collection(collection).document(doc_id)
            batch.set(doc_ref, converted)
            count += 1
            
            if count % 100 == 0:
                batch.commit()
                print(f"   ✓ Scritti {count} documenti...")
                batch = firestore_db.batch()
        except Exception as e:
            errors += 1
            print(f"   ⚠ Errore su doc {doc.get('_id')}: {e}")
    
    batch.commit()
    print(f"   ✅ Completato: {count} documenti migrati, {errors} errori")
    return {"migrated": count, "errors": errors}


def verify_firestore(firestore_db: firestore.Client, collection: str) -> int:
    """Verifica conteggio documenti in Firestore."""
    docs = list(firestore_db.collection(collection).limit(1000).get())
    return len(docs)


async def main_async(args):
    """Main async."""
    print("=" * 60)
    print("🗄️  Migrazione MongoDB → Firestore")
    print("=" * 60)
    print(f"   MongoDB: {MONGODB_URI}/{MONGODB_DB}")
    print(f"   Firestore: {args.project}/{FIRESTORE_DATABASE}")
    print(f"   Modalità: {'DRY-RUN' if args.dry_run else 'LIVE'}")
    
    mongo_client = AsyncIOMotorClient(MONGODB_URI)
    firestore_db = firestore.Client(project=args.project, database=FIRESTORE_DATABASE)
    
    collections_to_migrate = [args.collection] if args.collection else COLLECTIONS
    results = {}
    
    for coll in collections_to_migrate:
        results[coll] = await migrate_collection_async(
            mongo_client, firestore_db, coll, args.dry_run
        )
    
    if args.verify and not args.dry_run:
        print("\n" + "=" * 60)
        print("🔍 Verifica Firestore")
        print("=" * 60)
        for coll in collections_to_migrate:
            mongo_count = results[coll]["migrated"]
            firestore_count = verify_firestore(firestore_db, coll)
            status = "✅" if mongo_count == firestore_count else "⚠️"
            print(f"   {coll}: {firestore_count} documenti {status}")
    
    print("\n" + "=" * 60)
    print("✅ Migrazione completata!")
    print("=" * 60)
    
    mongo_client.close()


def main():
    parser = argparse.ArgumentParser(description="Migrazione MongoDB → Firestore")
    parser.add_argument("--collection", "-c", choices=COLLECTIONS, help="Collection specifica")
    parser.add_argument("--dry-run", action="store_true", help="Simula senza scrivere")
    parser.add_argument("--verify", action="store_true", help="Verifica dopo migrazione")
    parser.add_argument("--project", default=FIRESTORE_PROJECT, help="Project ID Firestore")
    args = parser.parse_args()
    
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()