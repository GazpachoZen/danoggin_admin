"""
UI tabs for the Danoggin Admin Tool
"""

# Import all tab classes for easier access
from .create_pack_tab import CreatePackTab
from .upload_questions_tab import UploadQuestionsTab
from .delete_packs_tab import DeletePacksTab
from .manage_users_tab import ManageUsersTab
from .purge_responder_status_tab import PurgeResponderStatusTab

__all__ = [
    'CreatePackTab',
    'UploadQuestionsTab', 
    'DeletePacksTab',
    'ManageUsersTab',
    'PurgeResponderStatusTab'
]