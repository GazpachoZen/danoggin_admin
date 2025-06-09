"""
Firebase Services Package for Danoggin Admin Tool

This package provides modular Firebase/Firestore operations split by domain:
- BaseFirebaseManager: Core Firebase connection and initialization
- QuestionPackManager: Question pack CRUD operations
- UserManager: User management and relationships
- StatusManager: Responder status and check-in data
- AnalyticsManager: Engagement metrics and analytics

Usage:
    from firebase_services import FirebaseManager
    
    # FirebaseManager is a facade that provides access to all managers
    firebase_manager = FirebaseManager()
    firebase_manager.initialize()
    
    # Access individual managers
    firebase_manager.question_packs.create_question_pack("test_pack")
    firebase_manager.users.delete_user("user123")
"""

from .base_manager import BaseFirebaseManager
from .question_pack_manager import QuestionPackManager
from .user_manager import UserManager
from .status_manager import StatusManager
from .analytics_manager import AnalyticsManager
from .fcm_manager import FCMManager

class FirebaseManager:
    """
    Facade class that provides a unified interface to all Firebase managers.
    
    This maintains backward compatibility with the original FirebaseManager
    while providing access to the new modular structure.
    """
    
    def __init__(self, service_account_path="resources/danoggin_service_account.json"):
        # Initialize the base manager
        self.base_manager = BaseFirebaseManager(service_account_path)
        
        # Initialize all domain managers
        self.question_packs = QuestionPackManager(self.base_manager)
        self.users = UserManager(self.base_manager)
        self.status = StatusManager(self.base_manager)
        self.analytics = AnalyticsManager(self.base_manager)
        self.fcm = FCMManager(self.base_manager)

        # Maintain backward compatibility by exposing service_account_path
        self.service_account_path = service_account_path
    
    def initialize(self):
        """Initialize Firebase connection"""
        return self.base_manager.initialize()
    
    # Backward compatibility methods - delegate to appropriate managers
    
    # Question Pack methods
    def create_question_pack(self, pack_name):
        return self.question_packs.create_question_pack(pack_name)
    
    def get_question_packs(self):
        return self.question_packs.get_question_packs()
    
    def get_question_packs_with_counts(self):
        return self.question_packs.get_question_packs_with_counts()
    
    def upload_questions(self, pack_name, questions_data):
        return self.question_packs.upload_questions(pack_name, questions_data)
    
    def delete_question_pack(self, pack_id):
        return self.question_packs.delete_question_pack(pack_id)
    
    # User methods
    def get_users_with_relationships(self):
        return self.users.get_users_with_relationships()
    
    def delete_user(self, user_id):
        return self.users.delete_user(user_id)
    
    def get_users_with_engagement_metrics(self):
        return self.users.get_users_with_engagement_metrics()
    
    def identify_test_accounts(self, include_criteria=None):
        return self.users.identify_test_accounts(include_criteria)
    
    # Status methods
    def get_responder_status_data(self):
        return self.status.get_responder_status_data()
    
    def get_responder_check_ins(self, responder_id, limit=20):
        return self.status.get_responder_check_ins(responder_id, limit)
    
    def purge_responder_status(self, responder_id):
        return self.status.purge_responder_status(responder_id)
    
    # Analytics methods
    def get_engagement_summary(self):
        return self.analytics.get_engagement_summary()
    
    # Cleanup method
    def _cleanup_resources(self):
        return self.base_manager._cleanup_resources()


# Export the main FirebaseManager for backward compatibility
__all__ = [
    'FirebaseManager',
    'BaseFirebaseManager',
    'QuestionPackManager', 
    'UserManager',
    'StatusManager',
    'AnalyticsManager',
    'FCMManager'
]