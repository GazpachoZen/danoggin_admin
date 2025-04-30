#!/usr/bin/env python
# firebase_test.py - Diagnostic tool for Danoggin Firebase database

import sys
import os
import firebase_admin
from firebase_admin import credentials, firestore


def print_separator():
    """Print a separator line for better readability"""
    print("=" * 80)


def initialize_firebase(service_account_path):
    """Initialize Firebase with the given service account"""
    print(f"Initializing Firebase with service account: {service_account_path}")

    if not os.path.exists(service_account_path):
        print(f"ERROR: Service account file not found at {service_account_path}")
        return None

    try:
        # Initialize Firebase app
        cred = credentials.Certificate(service_account_path)
        app = firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase initialized successfully")
        return db
    except Exception as e:
        print(f"ERROR initializing Firebase: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None


def list_collections(db):
    """List all top-level collections in the database"""
    print_separator()
    print("LISTING TOP-LEVEL COLLECTIONS")
    print_separator()

    try:
        collections = [collection.id for collection in db.collections()]
        print(f"Found {len(collections)} collections:")
        for i, collection_id in enumerate(collections, 1):
            print(f"{i}. {collection_id}")
        return collections
    except Exception as e:
        print(f"ERROR listing collections: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []


def list_responder_status(db):
    """List all documents in the responder_status collection"""
    print_separator()
    print("LISTING RESPONDER_STATUS DOCUMENTS")
    print_separator()

    try:
        # Get reference to responder_status collection
        # responder_status_ref = db.collection('responder_status')
        responder_status_ref = db.collection('responder_status')

        # Get all documents
        print("Retrieving all documents from responder_status collection...")
        docs = responder_status_ref.get()
        doc_list = list(docs)

        print(f"Found {len(doc_list)} documents in responder_status collection")

        # Print details of each document
        for i, doc in enumerate(doc_list, 1):
            responder_id = doc.id
            print(f"\nDocument {i}: ID = {responder_id}")

            # Get document data
            data = doc.to_dict()
            if data:
                print(f"Document data: {data}")
            else:
                print("Document has no data fields")

            # Get and list check-ins collection
            try:
                check_ins_ref = responder_status_ref.document(responder_id).collection('check_ins')
                check_ins = check_ins_ref.get()
                check_ins_list = list(check_ins)

                print(f"Found {len(check_ins_list)} check-ins:")

                # Print details of first few check-ins (limit to 3 for readability)
                for j, check_in in enumerate(check_ins_list[:3], 1):
                    check_in_data = check_in.to_dict()
                    print(f"  Check-in {j}: ID = {check_in.id}")

                    # Print timestamp if available
                    if 'timestamp' in check_in_data:
                        print(f"  Timestamp: {check_in_data['timestamp']}")

                    # Print other key fields
                    if 'result' in check_in_data:
                        print(f"  Result: {check_in_data['result']}")

                if len(check_ins_list) > 3:
                    print(f"  ... and {len(check_ins_list) - 3} more check-ins")

            except Exception as e:
                print(f"ERROR accessing check-ins for {responder_id}: {str(e)}")

    except Exception as e:
        print(f"ERROR listing responder_status documents: {str(e)}")
        import traceback
        print(traceback.format_exc())


def main():
    # Default service account path
    service_account_path = "resources/danoggin_service_account.json"

    # Allow overriding from command line
    if len(sys.argv) > 1:
        service_account_path = sys.argv[1]

    # Initialize Firebase
    db = initialize_firebase(service_account_path)
    if not db:
        print("Failed to initialize Firebase. Exiting.")
        return

    # List collections
    collections = list_collections(db)

    # Check if responder_status exists
    if 'responder_status' in collections:
        list_responder_status(db)
    else:
        print("\nresponder_status collection not found!")

    print("\nDiagnostic test completed.")


if __name__ == "__main__":
    main()