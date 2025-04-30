# # # # # # # # # # # # # # # # # # # # # # # # # # # 
#   BlueVista Solutions            
#   Company proprietary      Author: John Ivory
#   All rights reserved     Created: 4/28/2025, 9:17 AM
#   Copyright 2025
# # # # # # # # # # # # # # # # # # # # # # # # # # #
# !/usr/bin/env python
# danoggin_admin_gui.py

import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTabWidget, QFileDialog, QGroupBox)
from PyQt5.QtCore import QSize

# Import custom modules
from firebase_manager import FirebaseManager
from create_pack_tab import CreatePackTab
from upload_questions_tab import UploadQuestionsTab
from delete_packs_tab import DeletePacksTab
from manage_users_tab import ManageUsersTab
from purge_responder_status_tab import PurgeResponderStatusTab


class DanogginAdminApp(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.firebase_manager = FirebaseManager()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Danoggin Admin Tool")
        self.setMinimumSize(QSize(600, 400))

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create tabs
        self.tab_widget = QTabWidget()

        self.create_pack_tab = CreatePackTab(self.firebase_manager)
        self.tab_widget.addTab(self.create_pack_tab, "Create Pack")

        self.upload_questions_tab = UploadQuestionsTab(self.firebase_manager)
        self.tab_widget.addTab(self.upload_questions_tab, "Upload Questions")

        self.delete_packs_tab = DeletePacksTab(self.firebase_manager)
        self.tab_widget.addTab(self.delete_packs_tab, "Delete Packs")

        self.manage_users_tab = ManageUsersTab(self.firebase_manager)
        self.tab_widget.addTab(self.manage_users_tab, "Manage Users")

        self.purge_responder_status_tab = PurgeResponderStatusTab(self.firebase_manager)
        self.tab_widget.addTab(self.purge_responder_status_tab, "Purge Status Data")

        main_layout.addWidget(self.tab_widget)

        # Service account settings
        settings_group = QGroupBox("Firebase Settings")
        settings_layout = QHBoxLayout()

        self.service_account_input = QLineEdit("resources/danoggin_service_account.json")
        self.browse_sa_btn = QPushButton("Browse...")
        self.browse_sa_btn.clicked.connect(self.browse_service_account)

        settings_layout.addWidget(QLabel("Service Account:"))
        settings_layout.addWidget(self.service_account_input, 1)
        settings_layout.addWidget(self.browse_sa_btn)

        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # Initialize Firebase status
        self.status_bar = self.statusBar()
        self.check_firebase_connection()

    def browse_service_account(self):
        """Open a file dialog to select a service account file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Service Account JSON", "", "JSON Files (*.json)"
        )

        if file_path:
            self.service_account_input.setText(file_path)
            self.firebase_manager.service_account_path = file_path
            self.check_firebase_connection()

    def check_firebase_connection(self):
        """Check connection to Firebase and update status"""
        path = self.service_account_input.text().strip()
        if not os.path.exists(path):
            self.status_bar.showMessage("⚠️ Service account file not found!")
            return

        self.firebase_manager.service_account_path = path
        if self.firebase_manager.initialize():
            self.status_bar.showMessage("✅ Connected to Firebase")
        else:
            self.status_bar.showMessage("❌ Failed to connect to Firebase")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DanogginAdminApp()
    window.show()
    sys.exit(app.exec_())