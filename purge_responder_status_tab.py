# # # # # # # # # # # # # # # # # # # # # # # # # # # 
#   BlueVista Solutions            
#   Company proprietary      Author: Claude
#   All rights reserved     Created: 4/30/2025, 10:15 AM
#   Copyright 2025
# # # # # # # # # # # # # # # # # # # # # # # # # # #
# purge_responder_status_tab.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGroupBox, QTextEdit, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView, QCheckBox, QSplitter)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QBrush
import datetime


class PurgeResponderStatusTab(QWidget):
    """Tab for purging responder_status entries"""

    def __init__(self, firebase_manager):
        super().__init__()
        self.firebase_manager = firebase_manager
        self.responder_data = []  # Will store responder status information
        self.user_data = {}  # Will store user information for quick lookups
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Create splitter for table and details
        splitter = QSplitter(Qt.Vertical)

        # Responder status table (top section)
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)

        self.responders_table = QTableWidget()
        self.responders_table.setColumnCount(6)
        self.responders_table.setHorizontalHeaderLabels([
            "Select", "Responder ID", "Name", "Check-ins", "Latest Check-in", "Status"
        ])

        # Set column widths
        self.responders_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.responders_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.responders_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.responders_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.responders_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.responders_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.responders_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.responders_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.responders_table.itemSelectionChanged.connect(self.on_responder_selected)

        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self.refresh_responders)

        table_layout.addWidget(QLabel("Responder Status Records:"))
        table_layout.addWidget(self.responders_table)
        table_layout.addWidget(refresh_btn)

        splitter.addWidget(table_widget)

        # Details section (bottom)
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(QLabel("Check-in Details:"))
        details_layout.addWidget(self.details_text)

        splitter.addWidget(details_widget)

        # Set initial splitter size
        splitter.setSizes([300, 200])

        layout.addWidget(splitter, 1)

        # Action buttons
        actions_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all_responders)

        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all_responders)

        self.select_orphaned_btn = QPushButton("Select Orphaned")
        self.select_orphaned_btn.clicked.connect(self.select_orphaned_responders)

        self.purge_selected_btn = QPushButton("Purge Selected Records")
        self.purge_selected_btn.setStyleSheet("background-color: #ffcccc;")
        self.purge_selected_btn.clicked.connect(self.purge_selected_responders)

        actions_layout.addWidget(self.select_all_btn)
        actions_layout.addWidget(self.deselect_all_btn)
        actions_layout.addWidget(self.select_orphaned_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.purge_selected_btn)
        layout.addLayout(actions_layout)

        # Status area
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.status_text)

        self.setLayout(layout)

        # Initial load
        self.refresh_responders()

    def refresh_responders(self):
        """Refresh the list of responder_status entries"""
        self.status_text.append("Loading responder status records...")
        self.details_text.clear()

        try:
            # Get all users first for reference
            users = self.firebase_manager.get_users_with_relationships()
            self.user_data = {user['id']: user for user in users}
            self.status_text.append(f"Loaded {len(users)} user records for reference")

            # Get responder_status data
            self.status_text.append("Fetching responder_status records...")
            responder_status_data = self.firebase_manager.get_responder_status_data()

            if not responder_status_data:
                self.status_text.append("No responder status records found or failed to load data")
                self.responders_table.setRowCount(0)
                self.responder_data = []
                return

            self.status_text.append(f"Successfully retrieved {len(responder_status_data)} responder status records")

            # Store the responder data
            self.responder_data = responder_status_data

            # Populate the table
            self.status_text.append("Populating table with responder data...")
            self.responders_table.setRowCount(len(responder_status_data))
            orphaned_count = 0

            for row, responder_info in enumerate(responder_status_data):
                responder_id = responder_info['id']
                check_ins = responder_info['check_ins']
                latest_check_in = responder_info['latest_check_in']

                # Get user name if exists
                user_exists = responder_id in self.user_data
                if not user_exists:
                    orphaned_count += 1

                user_name = self.user_data.get(responder_id, {}).get('name', 'Unknown')

                # Checkbox cell for selection
                checkbox = QTableWidgetItem()
                checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox.setCheckState(Qt.Unchecked)
                self.responders_table.setItem(row, 0, checkbox)

                # Responder ID cell
                id_item = QTableWidgetItem(responder_id)
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
                self.responders_table.setItem(row, 1, id_item)

                # Name cell
                name_item = QTableWidgetItem(user_name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                self.responders_table.setItem(row, 2, name_item)

                # Check-ins count cell
                count_item = QTableWidgetItem(str(check_ins))
                count_item.setTextAlignment(Qt.AlignCenter)
                count_item.setFlags(count_item.flags() & ~Qt.ItemIsEditable)
                self.responders_table.setItem(row, 3, count_item)

                # Latest check-in cell
                latest_item = QTableWidgetItem(latest_check_in)
                latest_item.setFlags(latest_item.flags() & ~Qt.ItemIsEditable)
                self.responders_table.setItem(row, 4, latest_item)

                # Status cell
                status_text = "Valid" if user_exists else "Orphaned"
                status_item = QTableWidgetItem(status_text)
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)

                # Highlight orphaned entries in red
                if not user_exists:
                    status_item.setBackground(QBrush(QColor(255, 200, 200)))

                self.responders_table.setItem(row, 5, status_item)

            self.status_text.append(
                f"Loaded {len(responder_status_data)} responder status records ({orphaned_count} orphaned)")

        except Exception as e:
            self.status_text.append(f"Error refreshing responder status data: {str(e)}")
            import traceback
            self.status_text.append(traceback.format_exc())

    def on_responder_selected(self):
        """Handle responder selection in the table"""
        selected_rows = self.responders_table.selectedIndexes()
        if not selected_rows:
            self.details_text.clear()
            return

        # Get the selected row
        row = selected_rows[0].row()
        responder_id = self.responders_table.item(row, 1).text()

        # Find the responder data
        responder_info = None
        for info in self.responder_data:
            if info['id'] == responder_id:
                responder_info = info
                break

        if not responder_info:
            return

        # Get detailed check-in data
        check_in_details = self.firebase_manager.get_responder_check_ins(responder_id)

        # Format details text
        details = f"Responder ID: {responder_id}\n"
        details += f"Total Check-ins: {len(check_in_details)}\n\n"

        if check_in_details:
            details += "Recent Check-ins:\n"
            for i, check_in in enumerate(check_in_details[:10]):  # Show only 10 recent check-ins
                details += f"{i + 1}. {check_in.get('timestamp', 'Unknown time')} - Result: {check_in.get('result', 'Unknown')}\n"
                if 'prompt' in check_in:
                    details += f"   Question: {check_in['prompt']}\n"
                details += "\n"

            if len(check_in_details) > 10:
                details += f"...and {len(check_in_details) - 10} more check-ins\n"
        else:
            details += "No check-in details available."

        self.details_text.setText(details)

    def select_all_responders(self):
        """Select all responders in the table"""
        for row in range(self.responders_table.rowCount()):
            item = self.responders_table.item(row, 0)
            if item:
                item.setCheckState(Qt.Checked)
        self.status_text.append("Selected all responder records")

    def deselect_all_responders(self):
        """Deselect all responders in the table"""
        for row in range(self.responders_table.rowCount()):
            item = self.responders_table.item(row, 0)
            if item:
                item.setCheckState(Qt.Unchecked)
        self.status_text.append("Deselected all responder records")

    def select_orphaned_responders(self):
        """Select only orphaned responders (those without a user record)"""
        count = 0
        for row in range(self.responders_table.rowCount()):
            status_item = self.responders_table.item(row, 5)
            if status_item and status_item.text() == "Orphaned":
                check_item = self.responders_table.item(row, 0)
                if check_item:
                    check_item.setCheckState(Qt.Checked)
                    count += 1
            else:
                check_item = self.responders_table.item(row, 0)
                if check_item:
                    check_item.setCheckState(Qt.Unchecked)

        self.status_text.append(f"Selected {count} orphaned responder records")

    def get_selected_responders(self):
        """Get the selected responder IDs"""
        selected = []
        for row in range(self.responders_table.rowCount()):
            checkbox = self.responders_table.item(row, 0)
            if checkbox and checkbox.checkState() == Qt.Checked:
                responder_id = self.responders_table.item(row, 1).text()
                responder_name = self.responders_table.item(row, 2).text()
                check_ins = self.responders_table.item(row, 3).text()
                selected.append((responder_id, responder_name, check_ins))
        return selected

    def purge_selected_responders(self):
        """Purge selected responder_status records"""
        selected = self.get_selected_responders()

        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one responder status record to purge")
            return

        # Calculate total check-ins that will be deleted
        total_check_ins = sum(int(count) for _, _, count in selected)

        # Confirmation dialog with list of responders to purge
        responder_list = "\n".join([f"• {name} ({id}): {count} check-ins" for id, name, count in selected])
        confirm = QMessageBox.question(
            self,
            "Confirm Purge",
            f"Are you sure you want to purge these {len(selected)} responder status records?\n\n"
            f"{responder_list}\n\n"
            f"This will delete a total of {total_check_ins} check-in records.\n"
            f"This action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            self.status_text.append("Purge cancelled")
            return

        # Purge the selected responder status records
        success_count = 0
        failed_count = 0

        for responder_id, responder_name, _ in selected:
            success, message = self.firebase_manager.purge_responder_status(responder_id)

            if success:
                self.status_text.append(f"✅ Purged status for '{responder_name}' ({responder_id})")
                success_count += 1
            else:
                self.status_text.append(f"❌ Failed to purge '{responder_name}' ({responder_id}): {message}")
                failed_count += 1

        # Summary message
        self.status_text.append(f"Purge complete: {success_count} succeeded, {failed_count} failed")

        # Refresh the list
        self.refresh_responders()