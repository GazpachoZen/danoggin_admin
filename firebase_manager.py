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
        """Delete a user and clean up all relationships and associated data

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

                # Delete the responder_status document and all its check-ins
                responder_status_ref = self._db.collection('responder_status').document(user_id)
                responder_status_doc = responder_status_ref.get()

                if responder_status_doc.exists:
                    # First, delete all check-ins
                    check_ins_ref = responder_status_ref.collection('check_ins')
                    check_ins = list(check_ins_ref.stream())

                    for check_in in check_ins:
                        check_in.reference.delete()

                    # Then delete the responder_status document itself
                    responder_status_ref.delete()
                    print(f"Deleted responder_status document and {len(check_ins)} check-ins for user {user_id}")

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

            # Delete the user document
            user_ref.delete()

            return True, f"User '{user_name}' deleted successfully with all relationships and responder status cleaned up"
        except Exception as e:
            return False, f"Error deleting user: {str(e)}"

    def get_responder_status_data(self):
        """Get all responder_status data with summarized check-in information

        Returns:
            List of dictionaries with responder status information
        """
        if not self._db:
            if not self.initialize():
                return []

        try:
            print("Starting to fetch responder_status data")

            # Get direct reference to the responder_status collection
            responder_status_ref = self._db.collection('responder_status')

            # Use get() instead of stream() to ensure all documents are retrieved
            all_docs = responder_status_ref.get()
            doc_list = list(all_docs)

            print(f"Found {len(doc_list)} documents in responder_status collection")
            if len(doc_list) == 0:
                print("WARNING: No documents found in responder_status collection!")
            else:
                # Print first few document IDs for debugging
                print("First few document IDs:")
                for i, doc in enumerate(doc_list[:5]):
                    print(f"- {doc.id}")
                    if i >= 4:
                        break

            result = []

            for doc in doc_list:
                responder_id = doc.id
                print(f"Processing responder ID: {responder_id}")

                try:
                    # Get check-ins subcollection
                    check_ins_ref = responder_status_ref.document(responder_id).collection('check_ins')

                    # Use get() instead of stream() to ensure all documents are retrieved
                    check_ins = check_ins_ref.get()
                    check_ins_list = list(check_ins)
                    check_ins_count = len(check_ins_list)

                    print(f"Found {check_ins_count} check-ins for responder {responder_id}")

                    # Get latest check-in if any exist
                    latest_check_in = "Never"
                    if check_ins_count > 0:
                        # Get latest by timestamp field
                        latest_docs = check_ins_ref.order_by('timestamp', direction='DESCENDING').limit(1).get()
                        latest_docs_list = list(latest_docs)
                        if latest_docs_list:
                            latest_data = latest_docs_list[0].to_dict()
                            print(f"Latest check-in data fields: {', '.join(latest_data.keys())}")
                            if 'timestamp' in latest_data:
                                latest_check_in = latest_data['timestamp']
                                print(f"Latest timestamp: {latest_check_in}")

                    # Add to result
                    result.append({
                        'id': responder_id,
                        'check_ins': check_ins_count,
                        'latest_check_in': latest_check_in
                    })

                except Exception as e:
                    print(f"Error processing check-ins for {responder_id}: {e}")
                    import traceback
                    print(traceback.format_exc())

                    # Still add the responder to the list, but with 0 check-ins
                    result.append({
                        'id': responder_id,
                        'check_ins': 0,
                        'latest_check_in': "Error: " + str(e)
                    })

            print(f"Successfully processed {len(result)} responder status records")
            return result

        except Exception as e:
            print(f"Error getting responder status data: {e}")
            import traceback
            print(traceback.format_exc())
            return []

    def get_responder_check_ins(self, responder_id, limit=20):
        """Get detailed check-in data for a specific responder

        Args:
            responder_id: ID of the responder
            limit: Maximum number of check-ins to retrieve

        Returns:
            List of check-in dictionaries
        """
        if not self._db:
            if not self.initialize():
                return []

        try:
            print(f"Fetching check-ins for responder ID: {responder_id}")

            # First verify the responder_status document exists
            doc_ref = self._db.collection('responder_status').document(responder_id)
            doc = doc_ref.get()

            if not doc.exists:
                print(f"Responder status document {responder_id} does not exist")
                return []

            # Query the check_ins subcollection
            check_ins_query = doc_ref.collection('check_ins') \
                .order_by('timestamp', direction='DESCENDING') \
                .limit(limit)

            docs = list(check_ins_query.stream())
            print(f"Found {len(docs)} check-in documents (limited to {limit})")

            result = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id  # Add document ID
                result.append(data)

            return result

        except Exception as e:
            print(f"Error getting check-ins for {responder_id}: {e}")
            import traceback
            print(traceback.format_exc())
            return []

    def purge_responder_status(self, responder_id):
        """Delete a responder_status document and all its check-ins

        Args:
            responder_id: ID of the responder status to purge

        Returns:
            Tuple (success, message)
        """
        if not self._db:
            if not self.initialize():
                return False, "Failed to initialize Firebase"

        try:
            print(f"Starting to purge responder status for ID: {responder_id}")

            # First, check if the responder_status document exists
            doc_ref = self._db.collection('responder_status').document(responder_id)
            doc = doc_ref.get()
            if not doc.exists:
                return False, f"Responder status for ID {responder_id} not found"

            # Get all check-ins for this responder
            print(f"Fetching check-ins subcollection")
            check_ins_ref = doc_ref.collection('check_ins')
            check_ins = list(check_ins_ref.stream())
            print(f"Found {len(check_ins)} check-in documents to delete")

            # Delete all check-in documents
            batch_size = 0
            batch = self._db.batch()

            for doc in check_ins:
                batch.delete(doc.reference)
                batch_size += 1

                # Firestore batch has a limit of 500 operations
                if batch_size >= 400:
                    print(f"Committing batch of {batch_size} deletions")
                    batch.commit()
                    batch = self._db.batch()
                    batch_size = 0

            # Commit any remaining operations
            if batch_size > 0:
                print(f"Committing final batch of {batch_size} deletions")
                batch.commit()

            # Delete the responder_status document itself
            print(f"Deleting responder_status document")
            doc_ref.delete()

            return True, f"Successfully purged responder status and {len(check_ins)} check-ins"

        except Exception as e:
            print(f"Error purging responder status: {e}")
            import traceback
            print(traceback.format_exc())
            return False, f"Error purging responder status: {str(e)}"

    # Add cleanup handler for app termination
    def _cleanup_resources(self):
        """Clean up any resources held by the FirebaseManager"""
        # Placeholder for any cleanup needed
        print("Cleaning up Firebase resources")

    def get_users_with_engagement_metrics(self):
        """Get all users with their relationship information and engagement metrics

        Returns:
            List of user data dictionaries with relationship and engagement information
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

                # Add engagement metrics
                engagement_metrics = user_data.get('engagementMetrics', {})
                user_info['engagement_score'] = engagement_metrics.get('engagementScore', 0)
                user_info['token_failure_count'] = engagement_metrics.get('tokenFailureCount', 0)
                user_info['successful_notification_count'] = engagement_metrics.get('successfulNotificationCount', 0)

                # Calculate token health ratio
                total_notifications = user_info['token_failure_count'] + user_info['successful_notification_count']
                if total_notifications > 0:
                    success_rate = (user_info['successful_notification_count'] / total_notifications) * 100
                    user_info[
                        'token_health'] = f"{user_info['successful_notification_count']}/{total_notifications} ({success_rate:.1f}%)"
                else:
                    user_info['token_health'] = "No data"

                # Add last activity timestamps
                if 'lastSuccessfulNotification' in engagement_metrics:
                    last_success = engagement_metrics['lastSuccessfulNotification']
                    if hasattr(last_success, 'timestamp'):
                        from datetime import datetime
                        dt = datetime.fromtimestamp(last_success.timestamp())
                        user_info['last_successful_notification'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        user_info['last_successful_notification'] = str(last_success)
                else:
                    user_info['last_successful_notification'] = 'Never'

                # Identify test accounts (names containing numbers)
                user_info['is_likely_test'] = any(char.isdigit() for char in user_info['name'])

                users.append(user_info)

            return users
        except Exception as e:
            print(f"Error fetching users with engagement metrics: {str(e)}")
            return []


    def get_engagement_summary(self):
        """Get summary statistics for user engagement

        Returns:
            Dictionary with engagement statistics
        """
        if not self._db:
            if not self.initialize():
                return {}

        try:
            users = self.get_users_with_engagement_metrics()

            if not users:
                return {}

            # Calculate summary statistics
            total_users = len(users)
            healthy_users = len([u for u in users if u['engagement_score'] > 90])
            declining_users = len([u for u in users if 50 <= u['engagement_score'] <= 90])
            churned_users = len([u for u in users if u['engagement_score'] < 50])
            test_accounts = len([u for u in users if u['is_likely_test']])

            # Token health statistics
            users_with_notifications = [u for u in users if u['successful_notification_count'] > 0]
            avg_success_rate = 0
            if users_with_notifications:
                total_successes = sum(u['successful_notification_count'] for u in users_with_notifications)
                total_failures = sum(u['token_failure_count'] for u in users_with_notifications)
                total_attempts = total_successes + total_failures
                if total_attempts > 0:
                    avg_success_rate = (total_successes / total_attempts) * 100

            return {
                'total_users': total_users,
                'healthy_users': healthy_users,
                'declining_users': declining_users,
                'churned_users': churned_users,
                'test_accounts': test_accounts,
                'avg_notification_success_rate': avg_success_rate,
                'users_with_activity': len(users_with_notifications)
            }
        except Exception as e:
            print(f"Error getting engagement summary: {str(e)}")
            return {}


    def identify_test_accounts(self, include_criteria=None):
        """Identify likely test accounts based on criteria

        Args:
            include_criteria: Additional criteria for test account identification

        Returns:
            List of user IDs that are likely test accounts
        """
        if not self._db:
            if not self.initialize():
                return []

        try:
            users = self.get_users_with_engagement_metrics()
            test_account_ids = []

            for user in users:
                is_test = False

                # Primary criteria: name contains numbers
                if user['is_likely_test']:
                    is_test = True

                # Additional criteria can be added here
                if include_criteria:
                    # Example: very low engagement score
                    if 'low_engagement' in include_criteria and user['engagement_score'] < 20:
                        is_test = True

                    # Example: no successful notifications despite being old account
                    if 'no_activity' in include_criteria and user['successful_notification_count'] == 0:
                        # Check if account is older than 7 days
                        if user.get('created_at') and user['created_at'] != 'Unknown':
                            from datetime import datetime, timedelta
                            try:
                                created_date = datetime.strptime(user['created_at'], '%Y-%m-%d %H:%M:%S')
                                if datetime.now() - created_date > timedelta(days=7):
                                    is_test = True
                            except:
                                pass

                if is_test:
                    test_account_ids.append(user['id'])

            return test_account_ids
        except Exception as e:
            print(f"Error identifying test accounts: {str(e)}")
            return []