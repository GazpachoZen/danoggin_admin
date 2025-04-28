# firebase_manager.py

import firebase_admin
from firebase_admin import credentials, firestore


class FirebaseManager:
    """Manager for Firebase/Firestore operations"""

    def __init__(self, service_account_path="resources/danoggin_service_account.json"):
        self.service_account_path = service_account_path
        self._app = None
        self._db = None

    def initialize(self):
        """Initialize Firebase if not already initialized"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(self.service_account_path)
                self._app = firebase_admin.initialize_app(cred)
            self._db = firestore.client()
            return True
        except Exception as e:
            print(f"Error initializing Firebase: {str(e)}")
            return False

    def create_question_pack(self, pack_name):
        """Create a new question pack in Firestore"""
        if not self._db:
            if not self.initialize():
                return False, "Failed to initialize Firebase"

        try:
            # Format pack name for display
            display_name = ' '.join(word.capitalize() for word in pack_name.split('_'))

            # Create pack data
            pack_data = {
                'name': display_name,
                'imageFolder': f'question_packs/{pack_name}/images',
                'questions': []
            }

            # Add the pack to Firestore
            self._db.collection('question_packs').document(pack_name).set(pack_data)

            return True, f"Created pack '{display_name}' with ID '{pack_name}'"
        except Exception as e:
            return False, f"Error creating question pack: {str(e)}"

    def get_question_packs(self):
        """Get all question packs from Firestore"""
        if not self._db:
            if not self.initialize():
                return []

        try:
            pack_refs = self._db.collection('question_packs').stream()
            packs = []
            for pack_ref in pack_refs:
                pack_data = pack_ref.to_dict()
                packs.append((pack_ref.id, pack_data.get('name', 'Unnamed')))
            return packs
        except Exception as e:
            print(f"Error getting question packs: {str(e)}")
            return []

    def upload_questions(self, pack_name, questions_data):
        """Upload questions to a question pack"""
        if not self._db:
            if not self.initialize():
                return False, "Failed to initialize Firebase"

        try:
            # Get reference to the question pack
            pack_ref = self._db.collection('question_packs').document(pack_name)
            doc = pack_ref.get()

            if not doc.exists:
                return False, f"Question pack '{pack_name}' does not exist!"

            # Get current pack data
            current_data = doc.to_dict()

            # Combine questions
            current_questions = current_data.get('questions', [])
            combined_questions = current_questions + questions_data

            # Update the question pack
            pack_ref.update({
                'questions': combined_questions
            })

            return True, f"Added {len(questions_data)} questions to '{pack_name}'"
        except Exception as e:
            return False, f"Error uploading questions: {str(e)}"