# # # # # # # # # # # # # # # # # # # # # # # # # # # 
#   BlueVista Solutions            
#   Company proprietary      Author: John Ivory
#   All rights reserved     Created: 4/26/2025, 1:29 PM
#   Copyright 2023                                                                   
# # # # # # # # # # # # # # # # # # # # # # # # # # #
import os
import json
import sys
import firebase_admin
from firebase_admin import credentials, storage, firestore


def debug_firebase(service_account_path):
    """Print detailed diagnostic information about Firebase configuration"""
    print("\n--- FIREBASE DIAGNOSTICS ---\n")

    # 1. Check if service account file exists
    print(f"Service account path: {service_account_path}")
    if not os.path.exists(service_account_path):
        print(f"ERROR: Service account file not found!")
        return
    print("✓ Service account file exists")

    # 2. Examine service account contents (omitting sensitive data)
    try:
        with open(service_account_path, 'r') as f:
            sa_data = json.load(f)
            print(f"\nService account details:")
            print(f"- Project ID: {sa_data.get('project_id')}")
            print(f"- Client Email: {sa_data.get('client_email')}")

            # Construct default bucket name
            default_bucket = f"{sa_data.get('project_id')}.appspot.com"
            print(f"- Default bucket name: {default_bucket}")
    except Exception as e:
        print(f"ERROR reading service account file: {e}")
        return

    # 3. Try to initialize Firebase
    try:
        print("\nInitializing Firebase...")
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        print("✓ Firebase initialized successfully")
    except Exception as e:
        print(f"ERROR initializing Firebase: {e}")

    # 4. Try to connect to Firestore
    try:
        print("\nConnecting to Firestore...")
        db = firestore.client()
        collections = db.collections()
        collection_ids = [col.id for col in collections]
        print(f"✓ Firestore connected. Available collections: {collection_ids}")

        # Try to read question packs
        if 'question_packs' in collection_ids:
            packs = db.collection('question_packs').stream()
            pack_count = sum(1 for _ in packs)
            print(f"✓ Found {pack_count} question packs in Firestore")
    except Exception as e:
        print(f"ERROR connecting to Firestore: {e}")

    # 5. Try to connect to Storage with explicit bucket
    try:
        print(f"\nAttempting to connect to Storage with bucket: {default_bucket}")
        app = firebase_admin.initialize_app(cred, {
            'storageBucket': default_bucket
        }, name='storage_app')
        bucket = storage.bucket(app=app)
        print(f"✓ Successfully connected to Storage bucket: {bucket.name}")

        # List some files in the bucket
        print("Listing files in bucket (max 5):")
        blobs = list(bucket.list_blobs(max_results=5))
        if blobs:
            for blob in blobs:
                print(f"- {blob.name}")
        else:
            print("No files found in bucket (empty bucket)")
    except Exception as e:
        print(f"ERROR connecting to Storage: {e}")

    # 6. Check GCP permissions
    print("\nVerifying service account permissions...")
    try:
        # Try to test minimal permissions
        print("- Storage permissions: Unknown (requires making API calls)")
        print("- Firestore permissions: Appears to have read access")
        print("\nNOTE: To verify Storage permissions, check IAM settings in Google Cloud Console")
        print("The service account should have 'Storage Admin' or at least 'Storage Object Admin' role")
    except Exception as e:
        print(f"ERROR checking permissions: {e}")

    print("\n--- END DIAGNOSTICS ---")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python firebase_debug.py path/to/serviceAccountKey.json")
        sys.exit(1)

    debug_firebase(sys.argv[1])