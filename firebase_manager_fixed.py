# # # # # # # # # # # # # # # # # # # # # # # # # # # 
#   BlueVista Solutions            
#   Company proprietary      Author: John Ivory
#   All rights reserved     Created: 4/26/2025, 1:30 PM
#   Copyright 2023                                                                   
# # # # # # # # # # # # # # # # # # # # # # # # # # #
import os
import json
import firebase_admin
from firebase_admin import credentials, storage, firestore
from typing import Optional, List, Dict, Any


class FirebaseManager:
    """Manages connections and operations with Firebase services"""

    def __init__(self, service_account_path: str, bucket_name: Optional[str] = None):
        """Initialize Firebase with service account credentials

        Args:
            service_account_path: Path to the Firebase service account JSON file
            bucket_name: Optional Firebase Storage bucket name. If not provided, will try to
                        determine from the service account.
        """
        try:
            # Load the service account credentials and extract project ID
            with open(service_account_path, 'r') as f:
                service_account_info = json.load(f)
                self.project_id = service_account_info.get('project_id')
                print(f"Project ID from service account: {self.project_id}")

            # If bucket_name not provided, construct from project_id
            if not bucket_name and self.project_id:
                bucket_name = f"{self.project_id}.appspot.com"
                print(f"Using derived bucket name: {bucket_name}")

            # Initialize credential
            self.cred = credentials.Certificate(service_account_path)

            # First, initialize for Firestore only
            self.app_firestore = firebase_admin.initialize_app(self.cred, name='firestore_app')
            self.db = firestore.client(app=self.app_firestore)
            print("Firestore initialized successfully")

            # Then initialize for Storage with explicit bucket
            if bucket_name:
                self.app_storage = firebase_admin.initialize_app(self.cred, {
                    'storageBucket': bucket_name
                }, name='storage_app')
                self.bucket = storage.bucket(app=self.app_storage)
                print(f"Storage initialized with bucket: {bucket_name}")
            else:
                print("WARNING: No bucket name available. Storage operations will fail.")
                self.bucket = None

        except Exception as e:
            print(f"Error during Firebase initialization: {e}")
            raise

    def upload_image(self, file_path: str, destination_path: str) -> Optional[str]:
        """Upload an image to Firebase Storage

        Args:
            file_path: Local path to the image file
            destination_path: Destination path in Firebase Storage

        Returns:
            Download URL if successful, None otherwise
        """
        if not self.bucket:
            print("Error: Storage bucket not initialized")
            return None

        try:
            print(f"Uploading file: {file_path}")
            print(f"Destination path: {destination_path}")

            # Normalize file path (convert forward slashes to OS-specific separators)
            normalized_path = os.path.normpath(file_path)

            # Check if file exists
            if not os.path.exists(normalized_path):
                print(f"Error: File does not exist at {normalized_path}")
                return None

            blob = self.bucket.blob(destination_path)
            blob.upload_from_filename(normalized_path)
            blob.make_public()  # Make the file publicly accessible

            # Get and print the URL to verify success
            url = blob.public_url
            print(f"Upload successful. Public URL: {url}")
            return url

        except Exception as e:
            print(f"Error uploading {file_path}: {str(e)}")
            return None

    def get_question_packs(self) -> List[Dict[str, Any]]:
        """Retrieve all question packs from Firestore

        Returns:
            List of question pack dictionaries
        """
        packs = []
        try:
            pack_refs = self.db.collection('question_packs').stream()
            for pack_ref in pack_refs:
                pack_data = pack_ref.to_dict()
                pack_data['id'] = pack_ref.id
                packs.append(pack_data)
            return packs
        except Exception as e:
            print(f"Error fetching question packs: {str(e)}")
            return []

    def update_question_pack(self, pack_id: str, data: Dict[str, Any]) -> bool:
        """Update a question pack in Firestore

        Args:
            pack_id: ID of the question pack to update
            data: Updated data dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            self.db.collection('question_packs').document(pack_id).set(data, merge=True)
            return True
        except Exception as e:
            print(f"Error updating question pack {pack_id}: {str(e)}")
            return False