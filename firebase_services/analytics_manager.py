# firebase_services/analytics_manager.py


class AnalyticsManager:
    """Manager for engagement metrics and analytics operations"""

    def __init__(self, base_manager):
        self.base_manager = base_manager

    @property
    def db(self):
        """Get the Firestore database client from base manager"""
        return self.base_manager.db

    def get_engagement_summary(self):
        """Get summary statistics for user engagement

        Returns:
            Dictionary with engagement statistics
        """
        try:
            # We need to get users with engagement metrics, but this is now in UserManager
            # We'll need to coordinate with UserManager for this
            from .user_manager import UserManager
            user_manager = UserManager(self.base_manager)
            users = user_manager.get_users_with_engagement_metrics()

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