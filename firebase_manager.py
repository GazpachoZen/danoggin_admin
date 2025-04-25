# # # # # # # # # # # # # # # # # # # # # # # # # # # 
#   BlueVista Solutions            
#   Company proprietary      Author: John Ivory
#   All rights reserved     Created: 4/25/2025, 9:00 AM
#   Copyright 2025
# # # # # # # # # # # # # # # # # # # # # # # # # # #

import os
import firebase_admin
from firebase_admin import credentials, storage, firestore
from typing import Optional, List, Dict, Any


class FirebaseManager:
    """Manages connections and operations with Firebase services"""

    def __init__(self, service_account_path: str):
        """Initialize Firebase with service account credentials

        Args:
            service_account_path: Path to the Firebase service account JSON file
        """
        self.cred = credentials.Certificate(service_account_path)
        self.app = firebase_admin.initialize_app(self.cred, {
            'storageBucket': 'YOUR-PROJECT-ID.appspot.com'  # Replace with your bucket
        })
        self.db = firestore.client()
        self.bucket = storage.bucket()
        print("Firebase initialized successfully")

    def upload_image(self, file_path: str, destination_path: str) -> Optional[str]:
        """Upload an image to Firebase Storage

        Args:
            file_path: Local path to the image file
            destination_path: Destination path in Firebase Storage

        Returns:
            Download URL if successful, None otherwise
        """
        try:
            blob = self.bucket.blob(destination_path)
            blob.upload_from_filename(file_path)
            blob.make_public()  # Make the file publicly accessible
            return blob.public_url
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


# Example usage
if __name__ == "__main__":
    # Path to your Firebase service account key file
    service_account_path = "path/to/serviceAccountKey.json"

    # Initialize Firebase
    firebase = FirebaseManager(service_account_path)

    # Test connection by listing question packs
    packs = firebase.get_question_packs()
    print(f"Found {len(packs)} question packs")
    for pack in packs:
        print(f"- {pack.get('name', 'Unnamed')} (ID: {pack.get('id', 'Unknown')})")