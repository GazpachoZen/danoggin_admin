import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGroupBox, QTextEdit, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView, QApplication, QTreeWidget,
                             QTreeWidgetItem, QSplitter, QFrame, QTabWidget,
                             QTableView, QDialog, QDialogButtonBox, QCheckBox,
                             QComboBox)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QBrush


class ManageUsersTab(QWidget):
    """Enhanced tab for managing responders and observers with engagement metrics"""

    # Signal for when data changes
    data_changed = pyqtSignal()

    def __init__(self, firebase_manager):
        super().__init__()
        self.firebase_manager = firebase_manager
        self.users_data = []  # Will store user information
        self.show_engagement_metrics = True  # Toggle for showing engagement columns
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Top control section with enhanced filters
        control_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("Refresh Users")
        self.refresh_btn.clicked.connect(self.refresh_users)

        # Filter controls
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "All Users",
            "Healthy Users (Score > 90)",
            "Declining Users (Score 50-90)",
            "Churned Users (Score < 50)",
            "Likely Test Accounts",
            "Real Users Only"
        ])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)

        # Toggle engagement metrics display
        self.toggle_metrics_btn = QPushButton("Hide Engagement Data")
        self.toggle_metrics_btn.clicked.connect(self.toggle_engagement_display)

        control_layout.addWidget(self.refresh_btn)
        control_layout.addWidget(QLabel("Filter:"))
        control_layout.addWidget(self.filter_combo)
        control_layout.addWidget(self.toggle_metrics_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)

        # Engagement summary section
        self.summary_group = QGroupBox("Engagement Summary")
        summary_layout = QHBoxLayout()
        self.summary_label = QLabel("Loading engagement data...")
        summary_layout.addWidget(self.summary_label)
        self.summary_group.setLayout(summary_layout)
        layout.addWidget(self.summary_group)

        # Create splitter for table and details
        splitter = QSplitter(Qt.Vertical)

        # Users table (top section)
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)

        self.users_table = QTableWidget()
        self.setup_table_headers()

        # Make the table sortable
        self.users_table.setSortingEnabled(True)

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

        # Engagement tab
        engagement_widget = QWidget()
        engagement_layout = QVBoxLayout(engagement_widget)
        self.engagement_text = QTextEdit()
        self.engagement_text.setReadOnly(True)
        engagement_layout.addWidget(self.engagement_text)
        self.details_tabs.addTab(engagement_widget, "Engagement Metrics")

        details_layout.addWidget(self.details_tabs)

        splitter.addWidget(details_widget)

        # Set initial splitter size
        splitter.setSizes([300, 200])

        layout.addWidget(splitter, 1)

        # Action buttons
        actions_layout = QHBoxLayout()

        # Enhanced action buttons
        self.select_test_accounts_btn = QPushButton("Select Test Accounts")
        self.select_test_accounts_btn.clicked.connect(self.select_test_accounts)
        self.select_test_accounts_btn.setStyleSheet("background-color: #ffffcc;")

        self.delete_user_btn = QPushButton("Delete Selected User")
        self.delete_user_btn.setStyleSheet("background-color: #ffcccc;")
        self.delete_user_btn.clicked.connect(self.delete_selected_user)
        self.delete_user_btn.setEnabled(False)  # Disabled initially

        actions_layout.addWidget(self.select_test_accounts_btn)
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

    def setup_table_headers(self):
        """Setup table headers based on current display mode"""
        if self.show_engagement_metrics:
            self.users_table.setColumnCount(8)
            headers = ["User ID", "Name", "Role", "Created", "Relationships",
                       "Engagement Score", "Token Health", "Last Activity"]
        else:
            self.users_table.setColumnCount(5)
            headers = ["User ID", "Name", "Role", "Created", "Relationships"]

        self.users_table.setHorizontalHeaderLabels(headers)

        # Make column headers bold and left-aligned
        bold_font = QFont()
        bold_font.setBold(True)

        for col in range(self.users_table.columnCount()):
            header_item = self.users_table.horizontalHeaderItem(col)
            header_item.setFont(bold_font)
            header_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Set column widths
        self.users_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        if self.show_engagement_metrics:
            self.users_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
            self.users_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
            self.users_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
            self.users_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        else:
            self.users_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)

    def refresh_users(self):
        """Refresh the list of users with engagement metrics"""
        self.status_text.append("Loading users with engagement data...")

        # Temporarily disable sorting to avoid issues while populating
        self.users_table.setSortingEnabled(False)

        # Clear the current selection
        self.users_table.clearSelection()
        self.delete_user_btn.setEnabled(False)
        self.user_info_text.clear()
        self.relations_tree.clear()
        self.engagement_text.clear()

        # Get users from Firebase with engagement metrics
        users = self.firebase_manager.get_users_with_engagement_metrics()

        if not users:
            self.status_text.append("No users found or failed to load users")
            self.users_table.setRowCount(0)
            self.users_data = []
            self.update_engagement_summary({})
            return

        # Store the users data
        self.users_data = users

        # Update engagement summary
        summary = self.firebase_manager.get_engagement_summary()
        self.update_engagement_summary(summary)

        # Populate the table
        self.populate_user_table(users)

        # Re-enable sorting after population
        self.users_table.setSortingEnabled(True)

        self.status_text.append(f"Loaded {len(users)} users with engagement metrics")

    def populate_user_table(self, users):
        """Populate the user table with the given user data"""
        self.users_table.setRowCount(len(users))

        for row, user_data in enumerate(users):
            # User ID
            id_item = QTableWidgetItem(user_data['id'])
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.users_table.setItem(row, 0, id_item)

            # Name with color coding for test accounts
            name_item = QTableWidgetItem(user_data['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            if user_data.get('is_likely_test', False):
                name_item.setBackground(QBrush(QColor(255, 255, 200)))  # Light yellow for test accounts
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

            rel_item = QTableWidgetItem()
            rel_item.setData(Qt.DisplayRole, rel_text)
            rel_item.setData(Qt.UserRole, rel_count)  # For sorting by count
            rel_item.setFlags(rel_item.flags() & ~Qt.ItemIsEditable)
            self.users_table.setItem(row, 4, rel_item)

            # Engagement metrics (if showing)
            if self.show_engagement_metrics:
                # Engagement Score with color coding
                score = user_data.get('engagement_score', 0)
                score_item = QTableWidgetItem()
                score_item.setData(Qt.DisplayRole, score)
                score_item.setData(Qt.UserRole, score)
                score_item.setFlags(score_item.flags() & ~Qt.ItemIsEditable)

                # Color code based on health
                if score > 90:
                    score_item.setBackground(QBrush(QColor(200, 255, 200)))  # Light green
                elif score >= 50:
                    score_item.setBackground(QBrush(QColor(255, 255, 200)))  # Light yellow
                elif score > 0:
                    score_item.setBackground(QBrush(QColor(255, 200, 200)))  # Light red
                else:
                    score_item.setBackground(QBrush(QColor(240, 240, 240)))  # Light gray for no data

                self.users_table.setItem(row, 5, score_item)

                # Token Health
                health_item = QTableWidgetItem(user_data.get('token_health', 'No data'))
                health_item.setFlags(health_item.flags() & ~Qt.ItemIsEditable)
                self.users_table.setItem(row, 6, health_item)

                # Last Activity
                activity_item = QTableWidgetItem(user_data.get('last_successful_notification', 'Never'))
                activity_item.setFlags(activity_item.flags() & ~Qt.ItemIsEditable)
                self.users_table.setItem(row, 7, activity_item)

    def update_engagement_summary(self, summary):
        """Update the engagement summary display"""
        if not summary:
            self.summary_label.setText("No engagement data available")
            return

        summary_text = (
            f"Total Users: {summary.get('total_users', 0)} | "
            f"Healthy: {summary.get('healthy_users', 0)} | "
            f"Declining: {summary.get('declining_users', 0)} | "
            f"Churned: {summary.get('churned_users', 0)} | "
            f"Test Accounts: {summary.get('test_accounts', 0)} | "
            f"Notification Success Rate: {summary.get('avg_notification_success_rate', 0):.1f}%"
        )
        self.summary_label.setText(summary_text)

    def toggle_engagement_display(self):
        """Toggle the display of engagement metrics columns"""
        self.show_engagement_metrics = not self.show_engagement_metrics

        if self.show_engagement_metrics:
            self.toggle_metrics_btn.setText("Hide Engagement Data")
        else:
            self.toggle_metrics_btn.setText("Show Engagement Data")

        # Rebuild table with new headers
        self.setup_table_headers()
        if self.users_data:
            self.populate_user_table(self.users_data)

    def apply_filter(self):
        """Apply the selected filter to the user list"""
        filter_text = self.filter_combo.currentText()

        if not self.users_data:
            return

        filtered_users = []

        for user in self.users_data:
            include_user = False

            if filter_text == "All Users":
                include_user = True
            elif filter_text == "Healthy Users (Score > 90)":
                include_user = user.get('engagement_score', 0) > 90
            elif filter_text == "Declining Users (Score 50-90)":
                score = user.get('engagement_score', 0)
                include_user = 50 <= score <= 90
            elif filter_text == "Churned Users (Score < 50)":
                include_user = user.get('engagement_score', 0) < 50
            elif filter_text == "Likely Test Accounts":
                include_user = user.get('is_likely_test', False)
            elif filter_text == "Real Users Only":
                include_user = not user.get('is_likely_test', False)

            if include_user:
                filtered_users.append(user)

        self.populate_user_table(filtered_users)
        self.status_text.append(f"Applied filter '{filter_text}': showing {len(filtered_users)} users")

    def select_test_accounts(self):
        """Select all rows that are likely test accounts"""
        if not self.users_data:
            return

        selected_count = 0
        self.users_table.clearSelection()

        for row in range(self.users_table.rowCount()):
            name_item = self.users_table.item(row, 1)
            if name_item and name_item.background().color() == QColor(255, 255, 200):  # Test account color
                self.users_table.selectRow(row)
                selected_count += 1

        self.status_text.append(f"Selected {selected_count} test accounts")

        if selected_count > 0:
            QMessageBox.information(
                self,
                "Test Accounts Selected",
                f"Selected {selected_count} likely test accounts.\n"
                f"Review the selection and use 'Delete Selected User' to remove them one by one."
            )

    def on_user_selected(self):
        """Handle user selection in the table"""
        selected_rows = self.users_table.selectedIndexes()
        if not selected_rows:
            self.delete_user_btn.setEnabled(False)
            self.user_info_text.clear()
            self.relations_tree.clear()
            self.engagement_text.clear()
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

        # Update engagement tab
        self.update_engagement_info(user_data)

    def update_user_info(self, user_data):
        """Update the user info text area"""
        info_text = f"User ID: {user_data['id']}\n"
        info_text += f"Name: {user_data['name']}\n"
        info_text += f"Role: {user_data['role']}\n"
        info_text += f"Likely Test Account: {'Yes' if user_data.get('is_likely_test', False) else 'No'}\n"

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

    def update_engagement_info(self, user_data):
        """Update the engagement metrics display"""
        engagement_text = "=== ENGAGEMENT METRICS ===\n\n"

        score = user_data.get('engagement_score', 0)
        engagement_text += f"Engagement Score: {score}\n"

        if score > 90:
            engagement_text += "Status: ✅ HEALTHY - High engagement\n"
        elif score >= 50:
            engagement_text += "Status: ⚠️ DECLINING - Moderate engagement\n"
        elif score > 0:
            engagement_text += "Status: ❌ CHURNED - Low engagement\n"
        else:
            engagement_text += "Status: ❔ NO DATA - New user or no activity\n"

        engagement_text += f"\n=== NOTIFICATION METRICS ===\n"
        engagement_text += f"Successful Notifications: {user_data.get('successful_notification_count', 0)}\n"
        engagement_text += f"Failed Notifications: {user_data.get('token_failure_count', 0)}\n"
        engagement_text += f"Token Health: {user_data.get('token_health', 'No data')}\n"
        engagement_text += f"Last Successful Notification: {user_data.get('last_successful_notification', 'Never')}\n"

        engagement_text += f"\n=== ACCOUNT ANALYSIS ===\n"
        engagement_text += f"Likely Test Account: {'Yes' if user_data.get('is_likely_test', False) else 'No'}\n"

        if user_data.get('is_likely_test', False):
            engagement_text += "Reason: Name contains numbers\n"

        # Add recommendations
        engagement_text += f"\n=== RECOMMENDATIONS ===\n"
        if user_data.get('is_likely_test', False):
            engagement_text += "• Consider deleting this test account\n"
        elif score == 0:
            engagement_text += "• New user - monitor for initial activity\n"
        elif score < 50:
            engagement_text += "• User may have churned - investigate last activity\n"
        elif score < 90:
            engagement_text += "• User engagement declining - check notification delivery\n"
        else:
            engagement_text += "• User is healthy and engaged ✅\n"

        self.engagement_text.setText(engagement_text)

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

        # Enhanced confirmation dialog with engagement info
        is_test = user_data.get('is_likely_test', False)
        score = user_data.get('engagement_score', 0)

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

        # Additional warning for non-test accounts
        test_warning = ""
        if not is_test and score > 50:
            test_warning = f"\n\n⚠️  WARNING: This appears to be a REAL USER (not a test account) with engagement score {score}!"
        elif is_test:
            test_warning = f"\n\n✓ This appears to be a test account (name contains numbers)"

        # Confirmation dialog
        confirm = QMessageBox.question(
            self,
            "Confirm User Deletion",
            f"Are you sure you want to delete this user?\n\n"
            f"Name: {user_name}\n"
            f"ID: {user_id}\n"
            f"Role: {user_role}\n"
            f"Engagement Score: {score}{relationship_info}{test_warning}\n\n"
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