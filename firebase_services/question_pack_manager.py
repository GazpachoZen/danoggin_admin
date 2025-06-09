# firebase_services/question_pack_manager.py


class QuestionPackManager:
    """Manager for question pack operations"""

    def __init__(self, base_manager):
        self.base_manager = base_manager

    @property
    def db(self):
        """Get the Firestore database client from base manager"""
        return self.base_manager.db

    def create_question_pack(self, pack_name):
        """Create a new question pack in Firestore"""
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
            self.db.collection('question_packs').document(pack_name).set(pack_data)

            return True, f"Created pack '{display_name}' with ID '{pack_name}'"
        except Exception as e:
            return False, f"Error creating question pack: {str(e)}"

    def get_question_packs(self):
        """Get all question packs from Firestore"""
        try:
            pack_refs = self.db.collection('question_packs').stream()
            packs = []
            for pack_ref in pack_refs:
                pack_data = pack_ref.to_dict()
                packs.append((pack_ref.id, pack_data.get('name', 'Unnamed')))
            return packs
        except Exception as e:
            print(f"Error getting question packs: {str(e)}")
            return []

    def get_question_packs_with_counts(self):
        """Get all question packs from Firestore with question counts

        Returns:
            List of tuples (pack_id, pack_name, question_count)
        """
        try:
            pack_refs = self.db.collection('question_packs').stream()
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

    def upload_questions(self, pack_name, questions_data):
        """Upload questions to a question pack"""
        try:
            # Get reference to the question pack
            pack_ref = self.db.collection('question_packs').document(pack_name)
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

    def delete_question_pack(self, pack_id):
        """Delete a question pack from Firestore

        Args:
            pack_id: ID of the question pack to delete

        Returns:
            Tuple (success, message)
        """
        try:
            # Get the pack first to verify it exists
            pack_ref = self.db.collection('question_packs').document(pack_id)
            pack_doc = pack_ref.get()

            if not pack_doc.exists:
                return False, f"Question pack '{pack_id}' does not exist"

            # Delete the pack
            pack_ref.delete()
            return True, f"Question pack '{pack_id}' deleted successfully"
        except Exception as e:
            return False, f"Error deleting question pack: {str(e)}"

