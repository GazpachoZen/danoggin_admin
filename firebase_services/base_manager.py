# firebase_services/base_manager.py

import firebase_admin
from firebase_admin import credentials, firestore


class BaseFirebaseManager:
    """Base manager for Firebase/Firestore operations - handles connection and initialization"""

    def __init__(self, service_account_path="resources/danoggin_service_account.json"):
        self.service_account_path = service_account_path
        self._app = None
        self._db = None

    def initialize(self):
        """Initialize Firebase if not already initialized"""
        try:
            if not firebase_admin._apps:
                print(f"Initializing Firebase with service account: {self.service_account_path}")
                cred = credentials.Certificate(self.service_account_path)
                self._app = firebase_admin.initialize_app(cred)
                print("Firebase app initialized successfully")
            else:
                print("Firebase app already initialized")

            self._db = firestore.client()
            print("Firestore client created successfully")

            # Test listing all collections
            collections = [collection.id for collection in self._db.collections()]
            print(f"Available collections: {collections}")

            # Specifically test responder_status access
            if 'responder_status' in collections:
                print("Found responder_status collection, testing access...")
                try:
                    # Try to get ALL documents from the collection
                    all_docs = self._db.collection('responder_status').get()
                    doc_list = list(all_docs)
                    print(f"Found {len(doc_list)} documents in responder_status collection")

                    if doc_list:
                        print("Document IDs in responder_status collection:")
                        for doc in doc_list:
                            print(f"- {doc.id}")

                        # Test check_ins subcollection on first document
                        first_doc_id = doc_list[0].id
                        print(f"Testing check_ins subcollection for document {first_doc_id}")

                        check_ins = self._db.collection('responder_status').document(first_doc_id).collection(
                            'check_ins').get()
                        check_ins_list = list(check_ins)

                        print(f"Found {len(check_ins_list)} documents in check_ins subcollection")
                        if check_ins_list:
                            print("First few check-in documents:")
                            for i, check_in in enumerate(check_ins_list[:3]):  # Show up to 3
                                print(f"- {check_in.id}: {check_in.to_dict()}")
                                if i >= 2:  # Only show first 3
                                    break
                    else:
                        print("Collection exists but contains no documents")
                except Exception as e:
                    print(f"Error accessing responder_status: {e}")
                    import traceback
                    print(traceback.format_exc())
            return True
        except Exception as e:
            print(f"Error initializing Firebase: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False

    @property
    def db(self):
        """Get the Firestore database client. Auto-initializes if not already initialized."""
        if not self._db:
            if not self.initialize():
                raise RuntimeError("Failed to initialize Firebase")
        return self._db

    def _cleanup_resources(self):
        """Clean up any resources held by the FirebaseManager"""
        print("Cleaning up Firebase resources")

