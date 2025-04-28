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

    # Add these methods to the FirebaseManager class in firebase_manager.py

    def get_question_packs_with_counts(self):
        """Get all question packs from Firestore with question counts

        Returns:
            List of tuples (pack_id, pack_name, question_count)
        """
        if not self._db:
            if not self.initialize():
                return []

        try:
            pack_refs = self._db.collection('question_packs').stream()
            packs = []
            for pack_ref in pack_refs:
                pack_data = pack_ref.to_dict()
                pack_id = pack_ref.id
                pack_name = pack_data.get('name', 'Unnamed')
                question_count = len(pack_data.get('questions', []))
                packs.append((pack_id, pack_name, question_count))
            return packs
        except Exception as e:
            print(f"Error fetching question packs: {str(e)}")
            return []

    def delete_question_pack(self, pack_id):
        """Delete a question pack from Firestore

        Args:
            pack_id: ID of the question pack to delete

        Returns:
            Tuple (success, message)
        """
        if not self._db:
            if not self.initialize():
                return False, "Failed to initialize Firebase"

        try:
            # Get the pack first to verify it exists
            pack_ref = self._db.collection('question_packs').document(pack_id)
            pack_doc = pack_ref.get()

            if not pack_doc.exists:
                return False, f"Question pack '{pack_id}' does not exist"

            # Delete the pack
            pack_ref.delete()
            return True, f"Question pack '{pack_id}' deleted successfully"
        except Exception as e:
            return False, f"Error deleting question pack: {str(e)}"

    # Add these methods to the FirebaseManager class in firebase_manager.py

    def get_users_with_relationships(self):
        """Get all users with their relationship information

        Returns:
            List of user data dictionaries with relationship information
        """
        if not self._db:
            if not self.initialize():
                return []

        try:
            # Get all users
            user_refs = self._db.collection('users').stream()
            users = []

            for user_ref in user_refs:
                user_data = user_ref.to_dict()
                user_id = user_ref.id

                # Basic user info
                user_info = {
                    'id': user_id,
                    'name': user_data.get('name', 'Unnamed'),
                    'role': user_data.get('role', 'unknown'),
                }

                # Add created timestamp if available
                if 'createdAt' in user_data:
                    created_at = user_data['createdAt']
                    # Handle Firestore timestamp objects
                    if hasattr(created_at, 'timestamp'):
                        from datetime import datetime
                        dt = datetime.fromtimestamp(created_at.timestamp())
                        user_info['created_at'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        user_info['created_at'] = str(created_at)

                # Add invite code for responders
                if user_data.get('role') == 'responder' and 'inviteCode' in user_data:
                    user_info['invite_code'] = user_data['inviteCode']

                # Add relationships
                if user_data.get('role') == 'responder' and 'linkedObservers' in user_data:
                    user_info['linked_observers'] = user_data['linkedObservers']

                if user_data.get('role') == 'observer' and 'observing' in user_data:
                    user_info['observing'] = user_data['observing']

                users.append(user_info)

            return users
        except Exception as e:
            print(f"Error fetching users: {str(e)}")
            return []

    def delete_user(self, user_id):
        """Delete a user and clean up all relationships

        Args:
            user_id: ID of the user to delete

        Returns:
            Tuple (success, message)
        """
        if not self._db:
            if not self.initialize():
                return False, "Failed to initialize Firebase"

        try:
            # Get the user to determine role and relationships
            user_ref = self._db.collection('users').document(user_id)
            user_doc = user_ref.get()

            if not user_doc.exists:
                return False, f"User with ID '{user_id}' does not exist"

            user_data = user_doc.to_dict()
            user_role = user_data.get('role')
            user_name = user_data.get('name', 'Unnamed')

            # Handle relationship cleanup
            if user_role == 'responder':
                # Get all observers linked to this responder
                linked_observers = user_data.get('linkedObservers', {})

                # Remove responder from each observer's 'observing' list
                for observer_id in linked_observers.keys():
                    observer_ref = self._db.collection('users').document(observer_id)
                    observer_doc = observer_ref.get()

                    if observer_doc.exists:
                        observer_data = observer_doc.to_dict()
                        observing = observer_data.get('observing', {})

                        # Remove this responder
                        if user_id in observing:
                            observing.pop(user_id)

                            # Update the observer document
                            observer_ref.update({
                                'observing': observing
                            })

                # Also delete any check-ins for this responder
                check_ins_ref = self._db.collection('responder_status').document(user_id)
                check_ins_doc = check_ins_ref.get()

                if check_ins_doc.exists:
                    # For simplicity, we'll delete the entire document
                    # In a more detailed implementation, you might want to delete all subcollections
                    check_ins_ref.delete()

            elif user_role == 'observer':
                # Get all responders this observer is watching
                observing = user_data.get('observing', {})

                # Remove observer from each responder's 'linkedObservers' list
                for responder_id in observing.keys():
                    responder_ref = self._db.collection('users').document(responder_id)
                    responder_doc = responder_ref.get()

                    if responder_doc.exists:
                        responder_data = responder_doc.to_dict()
                        linked_observers = responder_data.get('linkedObservers', {})

                        # Remove this observer
                        if user_id in linked_observers:
                            linked_observers.pop(user_id)

                            # Update the responder document
                            responder_ref.update({
                                'linkedObservers': linked_observers
                            })

            # Delete the user
            user_ref.delete()

            return True, f"User '{user_name}' deleted successfully with all relationships cleaned up"
        except Exception as e:
            return False, f"Error deleting user: {str(e)}"
