# # # # # # # # # # # # # # # # # # # # # # # # # # # 
#   BlueVista Solutions            
#   Company proprietary      Author: John Ivory
#   All rights reserved     Created: 4/28/2025, 9:26 AM
#   Copyright 2025                                                                   
# # # # # # # # # # # # # # # # # # # # # # # # # # #
# upload_questions_tab.py

import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QGroupBox, QTextEdit,
                             QComboBox, QFileDialog, QMessageBox)


class UploadQuestionsTab(QWidget):
    """Tab for uploading questions to existing packs"""

    def __init__(self, firebase_manager):
        super().__init__()
        self.firebase_manager = firebase_manager
        self.json_file_path = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Pack selection
        pack_group = QGroupBox("Select Question Pack")
        pack_layout = QVBoxLayout()

        self.pack_combo = QComboBox()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_packs)

        pack_select_layout = QHBoxLayout()
        pack_select_layout.addWidget(QLabel("Pack:"))
        pack_select_layout.addWidget(self.pack_combo, 1)
        pack_select_layout.addWidget(self.refresh_btn)

        pack_layout.addLayout(pack_select_layout)
        pack_group.setLayout(pack_layout)
        layout.addWidget(pack_group)

        # File selection
        file_group = QGroupBox("Select Questions File")
        file_layout = QHBoxLayout()

        self.file_path_label = QLineEdit()
        self.file_path_label.setReadOnly(True)
        self.file_path_label.setPlaceholderText("No file selected")

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_file)

        file_layout.addWidget(self.file_path_label, 1)
        file_layout.addWidget(self.browse_btn)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Upload button
        btn_layout = QHBoxLayout()
        self.upload_btn = QPushButton("Upload Questions")
        self.upload_btn.clicked.connect(self.upload_questions)
        btn_layout.addStretch()
        btn_layout.addWidget(self.upload_btn)
        layout.addLayout(btn_layout)

        # Status area
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.status_text)

        layout.addStretch()
        self.setLayout(layout)

        # Load initial packs
        self.refresh_packs()

    def refresh_packs(self):
        """Refresh the list of question packs"""
        self.pack_combo.clear()
        packs = self.firebase_manager.get_question_packs()

        if not packs:
            self.status_text.append("No question packs found or failed to load packs")
            return

        for pack_id, pack_name in packs:
            self.pack_combo.addItem(pack_name, pack_id)

        self.status_text.append(f"Loaded {len(packs)} question packs")

    def browse_file(self):
        """Open a file dialog to select a JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Questions JSON File", "", "JSON Files (*.json)"
        )

        if file_path:
            self.json_file_path = file_path
            self.file_path_label.setText(os.path.basename(file_path))

    def upload_questions(self):
        """Upload questions from the selected JSON file to the selected pack"""
        if not self.json_file_path:
            QMessageBox.warning(self, "Input Error", "Please select a JSON file")
            return

        if self.pack_combo.count() == 0:
            QMessageBox.warning(self, "Input Error", "No question packs available")
            return

        pack_id = self.pack_combo.currentData()

        try:
            # Read and parse JSON file
            with open(self.json_file_path, 'r') as file:
                questions_data = json.load(file)

            if not isinstance(questions_data, list):
                self.status_text.append("❌ Error: JSON file must contain a list of question objects")
                return

            # Upload questions
            success, message = self.firebase_manager.upload_questions(pack_id, questions_data)

            if success:
                self.status_text.append(f"✅ {message}")
                # Clear selected file
                self.json_file_path = None
                self.file_path_label.clear()
            else:
                self.status_text.append(f"❌ {message}")

        except json.JSONDecodeError as e:
            self.status_text.append(f"❌ Invalid JSON format: {str(e)}")
        except Exception as e:
            self.status_text.append(f"❌ Error: {str(e)}")