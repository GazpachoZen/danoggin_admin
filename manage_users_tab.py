import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGroupBox, QTextEdit, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView, QApplication, QTreeWidget,
                             QTreeWidgetItem, QSplitter, QFrame, QTabWidget,
                             QTableView, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QFont


class ManageUsersTab(QWidget):
    """Tab for managing responders and observers"""

    # Signal for when data changes
    data_changed = pyqtSignal()

    def __init__(self, firebase_manager):
        super().__init__()
        self.firebase_manager = firebase_manager
        self.users_data = []  # Will store user information
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Top control section
        control_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("Refresh Users")
        self.refresh_btn.clicked.connect(self.refresh_users)

        control_layout.addWidget(self.refresh_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)

        # Create splitter for table and details
        splitter = QSplitter(Qt.Vertical)

        # Users table (top section)
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels([
            "User ID", "Name", "Role", "Created", "Relationships"
        ])

        # Make column headers bold and left-aligned
        bold_font = QFont()
        bold_font.setBold(True)

        for col in range(self.users_table.columnCount()):
            header_item = self.users_table.horizontalHeaderItem(col)
            header_item.setFont(bold_font)
            header_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Make the table sortable
        self.users_table.setSortingEnabled(True)

        # Set column widths
        self.users_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)

        self.users_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.users_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.users_table.itemSelectionChanged.connect(self.on_user_selected)

        table_layout.addWidget(QLabel("Users:"))
        table_layout.addWidget(self.users_table)

        splitter.addWidget(table_widget)

        # Details section (bottom)
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)

        # User details
        self.details_tabs = QTabWidget()

        # User info tab
        user_info_widget = QWidget()
        user_info_layout = QVBoxLayout(user_info_widget)
        self.user_info_text = QTextEdit()
        self.user_info_text.setReadOnly(True)
        user_info_layout.addWidget(self.user_info_text)
        self.details_tabs.addTab(user_info_widget, "User Info")

        # Relationships tab
        relations_widget = QWidget()
        relations_layout = QVBoxLayout(relations_widget)
        self.relations_tree = QTreeWidget()
        self.relations_tree.setHeaderLabels(["Relationship", "User ID", "Name"])
        self.relations_tree.setColumnWidth(0, 150)
        self.relations_tree.setColumnWidth(1, 300)
        relations_layout.addWidget(self.relations_tree)
        self.details_tabs.addTab(relations_widget, "Relationships")

        details_layout.addWidget(self.details_tabs)

        splitter.addWidget(details_widget)

        # Set initial splitter size
        splitter.setSizes([300, 200])

        layout.addWidget(splitter, 1)

        # Action buttons
        actions_layout = QHBoxLayout()

        self.delete_user_btn = QPushButton("Delete Selected User")
        self.delete_user_btn.setStyleSheet("background-color: #ffcccc;")
        self.delete_user_btn.clicked.connect(self.delete_selected_user)
        self.delete_user_btn.setEnabled(False)  # Disabled initially

        actions_layout.addStretch()
        actions_layout.addWidget(self.delete_user_btn)
        layout.addLayout(actions_layout)

        # Status area
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.status_text)

        self.setLayout(layout)

        # Load initial users
        self.refresh_users()

    def refresh_users(self):
        """Refresh the list of users"""
        self.status_text.append("Loading users...")

        # Temporarily disable sorting to avoid issues while populating
        self.users_table.setSortingEnabled(False)

        # Clear the current selection
        self.users_table.clearSelection()
        self.delete_user_btn.setEnabled(False)
        self.user_info_text.clear()
        self.relations_tree.clear()

        # Get users from Firebase
        users = self.firebase_manager.get_users_with_relationships()

        if not users:
            self.status_text.append("No users found or failed to load users")
            self.users_table.setRowCount(0)
            self.users_data = []
            return

        # Store the users data
        self.users_data = users

        # Populate the table
        self.users_table.setRowCount(len(users))
        for row, user_data in enumerate(users):
            # User ID
            id_item = QTableWidgetItem(user_data['id'])
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.users_table.setItem(row, 0, id_item)

            # Name
            name_item = QTableWidgetItem(user_data['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.users_table.setItem(row, 1, name_item)

            # Role
            role_item = QTableWidgetItem(user_data['role'])
            role_item.setFlags(role_item.flags() & ~Qt.ItemIsEditable)
            self.users_table.setItem(row, 2, role_item)

            # Created timestamp
            created_item = QTableWidgetItem(user_data.get('created_at', 'Unknown'))
            created_item.setFlags(created_item.flags() & ~Qt.ItemIsEditable)
            self.users_table.setItem(row, 3, created_item)

            # Relationship summary
            rel_count = 0
            if user_data['role'] == 'responder':
                rel_count = len(user_data.get('linked_observers', {}))
                rel_text = f"{rel_count} observer{'s' if rel_count != 1 else ''}"
            else:  # observer
                rel_count = len(user_data.get('observing', {}))
                rel_text = f"Watching {rel_count} responder{'s' if rel_count != 1 else ''}"

            # Store the count as data for proper sorting
            rel_item = QTableWidgetItem()
            rel_item.setData(Qt.DisplayRole, rel_text)
            rel_item.setData(Qt.UserRole, rel_count)  # For sorting by count
            rel_item.setFlags(rel_item.flags() & ~Qt.ItemIsEditable)
            self.users_table.setItem(row, 4, rel_item)

        # Re-enable sorting after population
        self.users_table.setSortingEnabled(True)

        self.status_text.append(f"Loaded {len(users)} users")

    def on_user_selected(self):
        """Handle user selection in the table"""
        selected_rows = self.users_table.selectedIndexes()
        if not selected_rows:
            self.delete_user_btn.setEnabled(False)
            self.user_info_text.clear()
            self.relations_tree.clear()
            return

        self.delete_user_btn.setEnabled(True)

        # Get the selected row
        row = selected_rows[0].row()
        user_id = self.users_table.item(row, 0).text()

        # Find the user data
        user_data = None
        for user in self.users_data:
            if user['id'] == user_id:
                user_data = user
                break

        if not user_data:
            return

        # Update user info tab
        self.update_user_info(user_data)

        # Update relationships tab
        self.update_relationships_tree(user_data)

    def update_user_info(self, user_data):
        """Update the user info text area"""
        info_text = f"User ID: {user_data['id']}\n"
        info_text += f"Name: {user_data['name']}\n"
        info_text += f"Role: {user_data['role']}\n"

        if 'created_at' in user_data:
            info_text += f"Created: {user_data['created_at']}\n"

        if 'invite_code' in user_data and user_data['role'] == 'responder':
            info_text += f"Invite Code: {user_data['invite_code']}\n"

        # Add relationship counts
        if user_data['role'] == 'responder':
            observers = user_data.get('linked_observers', {})
            info_text += f"\nObservers: {len(observers)}\n"
            if observers:
                info_text += "Observer Names:\n"
                for observer_id, observer_name in observers.items():
                    info_text += f"• {observer_name} ({observer_id})\n"
        else:  # observer
            responders = user_data.get('observing', {})
            info_text += f"\nMonitoring: {len(responders)} responders\n"
            if responders:
                info_text += "Responder Names:\n"
                for responder_id, responder_name in responders.items():
                    info_text += f"• {responder_name} ({responder_id})\n"

        self.user_info_text.setText(info_text)

    def update_relationships_tree(self, user_data):
        """Update the relationships tree"""
        self.relations_tree.clear()

        if user_data['role'] == 'responder':
            # Responder's observers
            observers = user_data.get('linked_observers', {})
            root = QTreeWidgetItem(self.relations_tree, ["Observers"])
            root.setExpanded(True)

            for observer_id, observer_name in observers.items():
                item = QTreeWidgetItem(root, ["Is observed by", observer_id, observer_name])

        else:  # observer
            # Observer's responders
            responders = user_data.get('observing', {})
            root = QTreeWidgetItem(self.relations_tree, ["Monitoring"])
            root.setExpanded(True)

            for responder_id, responder_name in responders.items():
                item = QTreeWidgetItem(root, ["Is monitoring", responder_id, responder_name])

    def delete_selected_user(self):
        """Delete the selected user"""
        selected_rows = self.users_table.selectedIndexes()
        if not selected_rows:
            return

        # Get the selected row
        row = selected_rows[0].row()
        user_id = self.users_table.item(row, 0).text()
        user_name = self.users_table.item(row, 1).text()
        user_role = self.users_table.item(row, 2).text()

        # Find the user data
        user_data = None
        for user in self.users_data:
            if user['id'] == user_id:
                user_data = user
                break

        if not user_data:
            return

        # Get relationship information for the confirmation message
        relationship_info = ""
        if user_role == 'responder':
            observers = user_data.get('linked_observers', {})
            if observers:
                relationship_info = f"\n\nThis responder is being observed by {len(observers)} observer(s)."
                relationship_info += "\nDeleting this user will remove these observation relationships."
        else:  # observer
            responders = user_data.get('observing', {})
            if responders:
                relationship_info = f"\n\nThis observer is monitoring {len(responders)} responder(s)."
                relationship_info += "\nDeleting this user will remove these monitoring relationships."

        # Confirmation dialog
        confirm = QMessageBox.question(
            self,
            "Confirm User Deletion",
            f"Are you sure you want to delete this user?\n\n"
            f"Name: {user_name}\n"
            f"ID: {user_id}\n"
            f"Role: {user_role}{relationship_info}\n\n"
            f"This action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            self.status_text.append("Deletion cancelled")
            return

        # Delete the user
        success, message = self.firebase_manager.delete_user(user_id)

        if success:
            self.status_text.append(f"✅ {message}")
            # Refresh users list
            self.refresh_users()
            # Emit signal that data has changed
            self.data_changed.emit()
        else:
            self.status_text.append(f"❌ {message}")