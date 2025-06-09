# # # # # # # # # # # # # # # # # # # # # # # # # # # 
#   BlueVista Solutions            
#   Company proprietary      Author: John Ivory
#   All rights reserved     Created: 4/28/2025, 9:36 AM
#   Copyright 2025                                                                   
# # # # # # # # # # # # # # # # # # # # # # # # # # #
# delete_packs_tab.py

import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGroupBox, QTextEdit, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QCheckBox, QAbstractItemView)
from PyQt5.QtCore import Qt


class DeletePacksTab(QWidget):
    """Tab for deleting question packs"""

    def __init__(self, firebase_manager):
        super().__init__()
        self.firebase_manager = firebase_manager
        self.packs_data = []  # Will store (id, name, question_count)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Pack selection table
        table_group = QGroupBox("Available Question Packs")
        table_layout = QVBoxLayout()

        self.packs_table = QTableWidget()
        self.packs_table.setColumnCount(3)  # Checkbox, Name, Question Count
        self.packs_table.setHorizontalHeaderLabels(["Select", "Pack Name", "Questions"])
        self.packs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.packs_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        refresh_btn = QPushButton("Refresh Packs")
        refresh_btn.clicked.connect(self.refresh_packs)

        table_layout.addWidget(self.packs_table)
        table_layout.addWidget(refresh_btn)

        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # Delete button
        btn_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Delete Selected Packs")
        self.delete_btn.setStyleSheet("background-color: #ffcccc;")
        self.delete_btn.clicked.connect(self.delete_selected_packs)

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all_packs)

        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all_packs)

        btn_layout.addWidget(self.select_all_btn)
        btn_layout.addWidget(self.deselect_all_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.delete_btn)
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
        self.status_text.append("Loading question packs...")

        # Get packs from Firebase
        packs = self.firebase_manager.get_question_packs_with_counts()

        if not packs:
            self.status_text.append("No question packs found or failed to load packs")
            self.packs_table.setRowCount(0)
            self.packs_data = []
            return

        # Store the packs data
        self.packs_data = packs

        # Populate the table
        self.packs_table.setRowCount(len(packs))
        for row, (pack_id, pack_name, question_count) in enumerate(packs):
            # Checkbox cell
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox.setCheckState(Qt.Unchecked)
            self.packs_table.setItem(row, 0, checkbox)

            # Pack name cell
            name_item = QTableWidgetItem(pack_name)
            name_item.setData(Qt.UserRole, pack_id)  # Store ID as user data
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)  # Make non-editable
            self.packs_table.setItem(row, 1, name_item)

            # Question count cell
            count_item = QTableWidgetItem(str(question_count))
            count_item.setTextAlignment(Qt.AlignCenter)
            count_item.setFlags(count_item.flags() & ~Qt.ItemIsEditable)  # Make non-editable
            self.packs_table.setItem(row, 2, count_item)

        # Adjust column widths
        self.packs_table.setColumnWidth(0, 50)  # Checkbox column
        self.packs_table.setColumnWidth(2, 100)  # Count column

        self.status_text.append(f"Loaded {len(packs)} question packs")

    def select_all_packs(self):
        """Select all packs in the table"""
        for row in range(self.packs_table.rowCount()):
            item = self.packs_table.item(row, 0)
            if item:
                item.setCheckState(Qt.Checked)
        self.status_text.append("Selected all packs")

    def deselect_all_packs(self):
        """Deselect all packs in the table"""
        for row in range(self.packs_table.rowCount()):
            item = self.packs_table.item(row, 0)
            if item:
                item.setCheckState(Qt.Unchecked)
        self.status_text.append("Deselected all packs")

    def get_selected_packs(self):
        """Get the selected pack IDs and names"""
        selected = []
        for row in range(self.packs_table.rowCount()):
            checkbox = self.packs_table.item(row, 0)
            if checkbox and checkbox.checkState() == Qt.Checked:
                name_item = self.packs_table.item(row, 1)
                pack_id = name_item.data(Qt.UserRole)
                pack_name = name_item.text()
                selected.append((pack_id, pack_name))
        return selected

    def delete_selected_packs(self):
        """Delete the selected question packs"""
        selected_packs = self.get_selected_packs()

        if not selected_packs:
            QMessageBox.warning(self, "No Selection", "Please select at least one question pack to delete")
            return

        # Confirmation dialog with list of packs to delete
        pack_list = "\n".join([f"• {name}" for _, name in selected_packs])
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete these {len(selected_packs)} question packs?\n\n{pack_list}\n\nThis action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            self.status_text.append("Deletion cancelled")
            return

        # Delete the selected packs
        success_count = 0
        failed_count = 0

        for pack_id, pack_name in selected_packs:
            success, message = self.firebase_manager.delete_question_pack(pack_id)

            if success:
                self.status_text.append(f"✅ Deleted '{pack_name}'")
                success_count += 1
            else:
                self.status_text.append(f"❌ Failed to delete '{pack_name}': {message}")
                failed_count += 1

        # Summary message
        self.status_text.append(f"Deletion complete: {success_count} succeeded, {failed_count} failed")

        # Refresh the pack list
        self.refresh_packs()
