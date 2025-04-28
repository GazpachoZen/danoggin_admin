# # # # # # # # # # # # # # # # # # # # # # # # # # # 
#   BlueVista Solutions            
#   Company proprietary      Author: John Ivory
#   All rights reserved     Created: 4/28/2025, 9:25 AM
#   Copyright 2025
# # # # # # # # # # # # # # # # # # # # # # # # # # #
# create_pack_tab.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QGroupBox, QFormLayout,
                             QTextEdit, QMessageBox)


class CreatePackTab(QWidget):
    """Tab for creating new question packs"""

    def __init__(self, firebase_manager):
        super().__init__()
        self.firebase_manager = firebase_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Form for pack creation
        form_group = QGroupBox("Create Question Pack")
        form_layout = QFormLayout()

        self.pack_name_input = QLineEdit()
        self.pack_name_input.setPlaceholderText("e.g. cognitive_test_1")
        form_layout.addRow("Pack ID:", self.pack_name_input)

        self.preview_label = QLabel("Preview: ")
        form_layout.addRow("", self.preview_label)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Preview update on text change
        self.pack_name_input.textChanged.connect(self.update_preview)

        # Create button
        btn_layout = QHBoxLayout()
        self.create_btn = QPushButton("Create Pack")
        self.create_btn.clicked.connect(self.create_pack)
        btn_layout.addStretch()
        btn_layout.addWidget(self.create_btn)
        layout.addLayout(btn_layout)

        # Status area
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.status_text)

        layout.addStretch()
        self.setLayout(layout)

    def update_preview(self):
        """Update the preview text based on pack name input"""
        pack_name = self.pack_name_input.text().strip()
        if pack_name:
            display_name = ' '.join(word.capitalize() for word in pack_name.split('_'))
            image_folder = f"question_packs/{pack_name}/images"
            preview = f"Display Name: {display_name}\nImage Folder: {image_folder}"
        else:
            preview = ""
        self.preview_label.setText(preview)

    def create_pack(self):
        """Create a new question pack"""
        pack_name = self.pack_name_input.text().strip()
        if not pack_name:
            QMessageBox.warning(self, "Input Error", "Please enter a pack ID")
            return

        success, message = self.firebase_manager.create_question_pack(pack_name)

        if success:
            self.status_text.append(f"✅ {message}")
            self.pack_name_input.clear()
        else:
            self.status_text.append(f"❌ {message}")