# firebase_services/user_manager.py


class UserManager:
    """Manager for user operations and relationships"""

    def __init__(self, base_manager):
        self.base_manager = base_manager

    @property
    def db(self):
        """Get the Firestore database client from base manager"""
        return self.base_manager.db

    def get_users_with_relationships(self):
        """Get all users with their relationship information

        Returns:
            List of user data dictionaries with relationship information
        """
        try:
            # Get all users
            user_refs = self.db.collection('users').stream()
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
        try:
            # Get the user to determine role and relationships
            user_ref = self.db.collection('users').document(user_id)
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
                    observer_ref = self.db.collection('users').document(observer_id)
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
                responder_status_ref = self.db.collection('responder_status').document(user_id)
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
                    responder_ref = self.db.collection('users').document(responder_id)
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

    def get_users_with_engagement_metrics(self):
        """Get all users with their relationship information and engagement metrics

        Returns:
            List of user data dictionaries with relationship and engagement information
        """
        try:
            # Get all users
            user_refs = self.db.collection('users').stream()
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

    def identify_test_accounts(self, include_criteria=None):
        """Identify likely test accounts based on criteria

        Args:
            include_criteria: Additional criteria for test account identification

        Returns:
            List of user IDs that are likely test accounts
        """
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
        
