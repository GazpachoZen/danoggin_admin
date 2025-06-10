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
    """Enhanced tab for managing responders and observers with comprehensive FCM token health metrics"""

    # Signal for when data changes
    data_changed = pyqtSignal()

    def __init__(self, firebase_manager):
        super().__init__()
        self.firebase_manager = firebase_manager
        self.users_data = []  # Will store user information
        self.fcm_token_data = {}  # Will store FCM token health data per user
        self.show_engagement_metrics = True  # Toggle for showing engagement columns
        self.show_fcm_details = True  # Toggle for showing FCM token details
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Top control section with enhanced filters
        control_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("Refresh Users & FCM Data")
        self.refresh_btn.clicked.connect(self.refresh_users)

        # Filter controls
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "All Users",
            "Healthy Users (Score > 90)",
            "Declining Users (Score 50-90)", 
            "Churned Users (Score < 50)",
            "Users with Token Issues",
            "Users with Multiple Strikes",
            "Users with Recent Removals",
            "Likely Test Accounts",
            "Real Users Only"
        ])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)

        # Toggle display options
        self.toggle_metrics_btn = QPushButton("Hide Engagement Data")
        self.toggle_metrics_btn.clicked.connect(self.toggle_engagement_display)

        self.toggle_fcm_btn = QPushButton("Hide FCM Details")
        self.toggle_fcm_btn.clicked.connect(self.toggle_fcm_display)

        control_layout.addWidget(self.refresh_btn)
        control_layout.addWidget(QLabel("Filter:"))
        control_layout.addWidget(self.filter_combo)
        control_layout.addWidget(self.toggle_metrics_btn)
        control_layout.addWidget(self.toggle_fcm_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)

        # Enhanced summary section with FCM health overview
        self.summary_group = QGroupBox("System Health Overview")
        summary_layout = QVBoxLayout()
        
        # Main summary line
        self.summary_label = QLabel("Loading engagement and FCM data...")
        summary_layout.addWidget(self.summary_label)
        
        # FCM health summary line
        self.fcm_summary_label = QLabel("Loading FCM token health data...")
        summary_layout.addWidget(self.fcm_summary_label)
        
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

        # User details tabs
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

        # NEW: FCM Token Health tab
        fcm_widget = QWidget()
        fcm_layout = QVBoxLayout(fcm_widget)
        self.fcm_health_text = QTextEdit()
        self.fcm_health_text.setReadOnly(True)
        fcm_layout.addWidget(self.fcm_health_text)
        self.details_tabs.addTab(fcm_widget, "🔔 FCM Token Health")

        # NEW: Recent FCM Events tab
        fcm_events_widget = QWidget()
        fcm_events_layout = QVBoxLayout(fcm_events_widget)
        
        # FCM events table
        self.fcm_events_table = QTableWidget()
        self.fcm_events_table.setColumnCount(5)
        self.fcm_events_table.setHorizontalHeaderLabels([
            "Timestamp", "Event Type", "Reason", "Context", "Details"
        ])
        self.fcm_events_table.horizontalHeader().setStretchLastSection(True)
        fcm_events_layout.addWidget(self.fcm_events_table)
        
        self.details_tabs.addTab(fcm_events_widget, "📋 Recent FCM Events")

        details_layout.addWidget(self.details_tabs)

        splitter.addWidget(details_widget)

        # Set initial splitter size
        splitter.setSizes([300, 250])

        layout.addWidget(splitter, 1)

        # Enhanced action buttons
        actions_layout = QHBoxLayout()

        self.select_token_issues_btn = QPushButton("Select Users with Token Issues")
        self.select_token_issues_btn.clicked.connect(self.select_users_with_token_issues)
        self.select_token_issues_btn.setStyleSheet("background-color: #fff4cc;")

        self.select_test_accounts_btn = QPushButton("Select Test Accounts")
        self.select_test_accounts_btn.clicked.connect(self.select_test_accounts)
        self.select_test_accounts_btn.setStyleSheet("background-color: #ffffcc;")

        self.export_fcm_report_btn = QPushButton("📤 Export FCM Report")
        self.export_fcm_report_btn.clicked.connect(self.export_fcm_health_report)

        self.delete_user_btn = QPushButton("Delete Selected User")
        self.delete_user_btn.setStyleSheet("background-color: #ffcccc;")
        self.delete_user_btn.clicked.connect(self.delete_selected_user)
        self.delete_user_btn.setEnabled(False)  # Disabled initially

        actions_layout.addWidget(self.select_token_issues_btn)
        actions_layout.addWidget(self.select_test_accounts_btn)
        actions_layout.addWidget(self.export_fcm_report_btn)
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
        base_headers = ["User ID", "Name", "Role", "Created", "Relationships"]
        
        headers = base_headers.copy()
        
        if self.show_engagement_metrics:
            headers.extend(["Engagement\nScore", "Token\nHealth", "Last\nActivity"])
        
        if self.show_fcm_details:
            headers.extend(["FCM\nEvents", "Strikes", "Removals", "Token\nStatus"])

        self.users_table.setColumnCount(len(headers))
        self.users_table.setHorizontalHeaderLabels(headers)

        # Make column headers bold and left-aligned
        bold_font = QFont()
        bold_font.setBold(True)

        for col in range(self.users_table.columnCount()):
            header_item = self.users_table.horizontalHeaderItem(col)
            header_item.setFont(bold_font)
            header_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Set column widths
        for col in range(min(5, len(headers))):  # First 5 columns
            self.users_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        
        # Make the last column stretch
        if len(headers) > 0:
            self.users_table.horizontalHeader().setSectionResizeMode(len(headers) - 1, QHeaderView.Stretch)

    def refresh_users(self):
        """Refresh the list of users with engagement metrics and FCM token health data"""
        self.status_text.append("Loading users with engagement and FCM data...")

        # Temporarily disable sorting to avoid issues while populating
        self.users_table.setSortingEnabled(False)

        # Clear the current selection
        self.users_table.clearSelection()
        self.delete_user_btn.setEnabled(False)
        self.user_info_text.clear()
        self.relations_tree.clear()
        self.engagement_text.clear()
        self.fcm_health_text.clear()
        self.fcm_events_table.setRowCount(0)

        # Get users from Firebase with engagement metrics
        users = self.firebase_manager.get_users_with_engagement_metrics()

        if not users:
            self.status_text.append("No users found or failed to load users")
            self.users_table.setRowCount(0)
            self.users_data = []
            self.fcm_token_data = {}
            self.update_engagement_summary({})
            return

        # Store the users data
        self.users_data = users

        # Load FCM token health data for all users
        self.load_fcm_token_data()

        # Update summaries
        summary = self.firebase_manager.get_engagement_summary()
        self.update_engagement_summary(summary)
        self.update_fcm_summary()

        # Populate the table
        self.populate_user_table(users)

        # Re-enable sorting after population
        self.users_table.setSortingEnabled(True)

        self.status_text.append(f"Loaded {len(users)} users with engagement and FCM metrics")

    def load_fcm_token_data(self):
        """Load FCM token health data for all users"""
        try:
            self.status_text.append("Loading FCM token health data...")
            
            # Get users with token issues from the last 30 days
            users_with_issues = self.firebase_manager.fcm.get_users_with_token_issues(days=30)
            
            # Create a lookup dictionary for quick access
            self.fcm_token_data = {}
            
            for user_issue in users_with_issues:
                user_id = user_issue.get('userId', '')
                if user_id:
                    self.fcm_token_data[user_id] = user_issue
            
            # For each user, also get their detailed token health report
            for user in self.users_data:
                user_id = user['id']
                if user_id not in self.fcm_token_data:
                    # Initialize with empty data for users without issues
                    self.fcm_token_data[user_id] = {
                        'userId': user_id,
                        'userName': user.get('name', 'Unknown'),
                        'issues': [],
                        'total_removals': 0,
                        'total_strikes': 0,
                        'contexts': []
                    }
                
                # Get recent events count for all users
                try:
                    recent_events = self.firebase_manager.fcm.get_token_events_for_user(user_id, days=7)
                    self.fcm_token_data[user_id]['recent_events_count'] = len(recent_events)
                    self.fcm_token_data[user_id]['recent_events'] = recent_events
                except Exception as e:
                    self.fcm_token_data[user_id]['recent_events_count'] = 0
                    self.fcm_token_data[user_id]['recent_events'] = []
            
            self.status_text.append("FCM token health data loaded successfully")
            
        except Exception as e:
            self.status_text.append(f"Error loading FCM token data: {str(e)}")
            self.fcm_token_data = {}

    def populate_user_table(self, users):
        """Populate the user table with the given user data including FCM metrics"""
        self.users_table.setRowCount(len(users))

        for row, user_data in enumerate(users):
            col = 0
            
            # User ID
            id_item = QTableWidgetItem(user_data['id'])
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.users_table.setItem(row, col, id_item)
            col += 1

            # Name with color coding for test accounts
            name_item = QTableWidgetItem(user_data['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            if user_data.get('is_likely_test', False):
                name_item.setBackground(QBrush(QColor(255, 255, 200)))  # Light yellow for test accounts
            self.users_table.setItem(row, col, name_item)
            col += 1

            # Role
            role_item = QTableWidgetItem(user_data['role'])
            role_item.setFlags(role_item.flags() & ~Qt.ItemIsEditable)
            self.users_table.setItem(row, col, role_item)
            col += 1

            # Created timestamp
            created_item = QTableWidgetItem(user_data.get('created_at', 'Unknown'))
            created_item.setFlags(created_item.flags() & ~Qt.ItemIsEditable)
            self.users_table.setItem(row, col, created_item)
            col += 1

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
            self.users_table.setItem(row, col, rel_item)
            col += 1

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

                self.users_table.setItem(row, col, score_item)
                col += 1

                # Token Health
                health_item = QTableWidgetItem(user_data.get('token_health', 'No data'))
                health_item.setFlags(health_item.flags() & ~Qt.ItemIsEditable)
                self.users_table.setItem(row, col, health_item)
                col += 1

                # Last Activity
                activity_item = QTableWidgetItem(user_data.get('last_successful_notification', 'Never'))
                activity_item.setFlags(activity_item.flags() & ~Qt.ItemIsEditable)
                self.users_table.setItem(row, col, activity_item)
                col += 1

            # FCM details (if showing)
            if self.show_fcm_details:
                user_id = user_data['id']
                fcm_data = self.fcm_token_data.get(user_id, {})
                
                # Recent FCM Events count
                events_count = fcm_data.get('recent_events_count', 0)
                events_item = QTableWidgetItem()
                events_item.setData(Qt.DisplayRole, events_count)
                events_item.setData(Qt.UserRole, events_count)
                events_item.setFlags(events_item.flags() & ~Qt.ItemIsEditable)
                
                # Color code based on events count
                if events_count > 10:
                    events_item.setBackground(QBrush(QColor(255, 200, 200)))  # Light red for many events
                elif events_count > 3:
                    events_item.setBackground(QBrush(QColor(255, 255, 200)))  # Light yellow for some events
                
                self.users_table.setItem(row, col, events_item)
                col += 1
                
                # Strikes count
                strikes = fcm_data.get('total_strikes', 0)
                strikes_item = QTableWidgetItem()
                strikes_item.setData(Qt.DisplayRole, strikes)
                strikes_item.setData(Qt.UserRole, strikes)
                strikes_item.setFlags(strikes_item.flags() & ~Qt.ItemIsEditable)
                
                # Color code strikes
                if strikes >= 2:
                    strikes_item.setBackground(QBrush(QColor(255, 150, 150)))  # Red for multiple strikes
                elif strikes > 0:
                    strikes_item.setBackground(QBrush(QColor(255, 220, 150)))  # Orange for single strike
                
                self.users_table.setItem(row, col, strikes_item)
                col += 1
                
                # Removals count  
                removals = fcm_data.get('total_removals', 0)
                removals_item = QTableWidgetItem()
                removals_item.setData(Qt.DisplayRole, removals)
                removals_item.setData(Qt.UserRole, removals)
                removals_item.setFlags(removals_item.flags() & ~Qt.ItemIsEditable)
                
                # Color code removals
                if removals > 0:
                    removals_item.setBackground(QBrush(QColor(255, 180, 180)))  # Light red for any removals
                
                self.users_table.setItem(row, col, removals_item)
                col += 1
                
                # Token Status summary
                if events_count == 0 and strikes == 0 and removals == 0:
                    status = "Healthy"
                    status_color = QColor(200, 255, 200)  # Light green
                elif removals > 0 or strikes >= 2:
                    status = "Critical"
                    status_color = QColor(255, 150, 150)  # Red
                elif strikes > 0 or events_count > 5:
                    status = "Warning"
                    status_color = QColor(255, 220, 150)  # Orange
                else:
                    status = "Monitoring"
                    status_color = QColor(255, 255, 200)  # Light yellow
                
                status_item = QTableWidgetItem(status)
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                status_item.setBackground(QBrush(status_color))
                self.users_table.setItem(row, col, status_item)
                col += 1

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

    def update_fcm_summary(self):
        """Update the FCM health summary display"""
        if not self.fcm_token_data:
            self.fcm_summary_label.setText("No FCM token data available")
            return
        
        total_users = len(self.fcm_token_data)
        users_with_issues = len([data for data in self.fcm_token_data.values() 
                                if data.get('total_strikes', 0) > 0 or data.get('total_removals', 0) > 0])
        users_with_strikes = len([data for data in self.fcm_token_data.values() 
                                 if data.get('total_strikes', 0) > 0])
        users_with_removals = len([data for data in self.fcm_token_data.values() 
                                  if data.get('total_removals', 0) > 0])
        total_recent_events = sum(data.get('recent_events_count', 0) for data in self.fcm_token_data.values())
        
        health_percentage = ((total_users - users_with_issues) / total_users * 100) if total_users > 0 else 100
        
        fcm_summary_text = (
            f"FCM Health: {health_percentage:.1f}% | "
            f"Users with Issues: {users_with_issues}/{total_users} | "
            f"Users with Strikes: {users_with_strikes} | "
            f"Users with Removals: {users_with_removals} | "
            f"Recent Events (7d): {total_recent_events}"
        )
        self.fcm_summary_label.setText(fcm_summary_text)

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

    def toggle_fcm_display(self):
        """Toggle the display of FCM token health columns"""
        self.show_fcm_details = not self.show_fcm_details

        if self.show_fcm_details:
            self.toggle_fcm_btn.setText("Hide FCM Details")
        else:
            self.toggle_fcm_btn.setText("Show FCM Details")

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
            user_id = user['id']
            fcm_data = self.fcm_token_data.get(user_id, {})

            if filter_text == "All Users":
                include_user = True
            elif filter_text == "Healthy Users (Score > 90)":
                include_user = user.get('engagement_score', 0) > 90
            elif filter_text == "Declining Users (Score 50-90)":
                score = user.get('engagement_score', 0)
                include_user = 50 <= score <= 90
            elif filter_text == "Churned Users (Score < 50)":
                include_user = user.get('engagement_score', 0) < 50
            elif filter_text == "Users with Token Issues":
                include_user = (fcm_data.get('total_strikes', 0) > 0 or 
                               fcm_data.get('total_removals', 0) > 0 or 
                               fcm_data.get('recent_events_count', 0) > 5)
            elif filter_text == "Users with Multiple Strikes":
                include_user = fcm_data.get('total_strikes', 0) >= 2
            elif filter_text == "Users with Recent Removals":
                include_user = fcm_data.get('total_removals', 0) > 0
            elif filter_text == "Likely Test Accounts":
                include_user = user.get('is_likely_test', False)
            elif filter_text == "Real Users Only":
                include_user = not user.get('is_likely_test', False)

            if include_user:
                filtered_users.append(user)

        self.populate_user_table(filtered_users)
        self.status_text.append(f"Applied filter '{filter_text}': showing {len(filtered_users)} users")

    def select_users_with_token_issues(self):
        """Select all rows that have FCM token issues"""
        if not self.users_data:
            return

        selected_count = 0
        self.users_table.clearSelection()

        for row in range(self.users_table.rowCount()):
            user_id_item = self.users_table.item(row, 0)
            if user_id_item:
                user_id = user_id_item.text()
                fcm_data = self.fcm_token_data.get(user_id, {})
                
                # Check if user has token issues
                has_issues = (fcm_data.get('total_strikes', 0) > 0 or 
                             fcm_data.get('total_removals', 0) > 0 or 
                             fcm_data.get('recent_events_count', 0) > 5)
                
                if has_issues:
                    self.users_table.selectRow(row)
                    selected_count += 1

        self.status_text.append(f"Selected {selected_count} users with FCM token issues")

        if selected_count > 0:
            QMessageBox.information(
                self,
                "Users with Token Issues Selected",
                f"Selected {selected_count} users with FCM token issues.\n"
                f"These users have strikes, removals, or high event counts."
            )

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
            self.fcm_health_text.clear()
            self.fcm_events_table.setRowCount(0)
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

        # Update FCM health tab
        self.update_fcm_health_info(user_data)

        # Update FCM events tab
        self.update_fcm_events_table(user_data)

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

        info_text += "\n\n=================================="
        info_text += f"\nfcmToken: {user_data['fcmToken']}"
        info_text += f"\nnextCheckInTime: {user_data['nextCheckInTime']}"
        info_text += f"\nlastCheckInTime: {user_data['lastCheckInTime']}"
        
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

    def update_fcm_health_info(self, user_data):
        """Update the FCM token health display"""
        user_id = user_data['id']
        fcm_data = self.fcm_token_data.get(user_id, {})
        
        fcm_text = "=== FCM TOKEN HEALTH REPORT ===\n\n"
        
        # Overall status
        recent_events = fcm_data.get('recent_events_count', 0)
        strikes = fcm_data.get('total_strikes', 0)
        removals = fcm_data.get('total_removals', 0)
        
        if recent_events == 0 and strikes == 0 and removals == 0:
            fcm_text += "🟢 STATUS: HEALTHY\n"
            fcm_text += "No token issues detected in the last 30 days.\n\n"
        elif removals > 0 or strikes >= 2:
            fcm_text += "🔴 STATUS: CRITICAL\n"
            fcm_text += "User has significant token delivery issues.\n\n"
        elif strikes > 0 or recent_events > 5:
            fcm_text += "🟡 STATUS: WARNING\n"
            fcm_text += "User has some token delivery issues.\n\n"
        else:
            fcm_text += "🔵 STATUS: MONITORING\n"
            fcm_text += "Minor issues detected, monitoring required.\n\n"
        
        # Token event summary
        fcm_text += "=== TOKEN EVENT SUMMARY (30 days) ===\n"
        fcm_text += f"Recent Events (7 days): {recent_events}\n"
        fcm_text += f"Total Strikes: {strikes}\n"
        fcm_text += f"Total Removals: {removals}\n"
        
        # Issue breakdown
        issues = fcm_data.get('issues', [])
        if issues:
            fcm_text += f"Total Issues: {len(issues)}\n\n"
            
            fcm_text += "=== ISSUE BREAKDOWN ===\n"
            issue_types = {}
            for issue in issues:
                issue_type = issue.get('type', 'unknown')
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
            
            for issue_type, count in issue_types.items():
                fcm_text += f"• {issue_type}: {count} occurrences\n"
        else:
            fcm_text += "Total Issues: 0\n"
        
        # Contexts where issues occurred
        contexts = fcm_data.get('contexts', [])
        if contexts:
            fcm_text += f"\n=== AFFECTED NOTIFICATION CONTEXTS ===\n"
            for context in contexts:
                fcm_text += f"• {context}\n"
        
        # Recommendations based on FCM health
        fcm_text += f"\n=== FCM HEALTH RECOMMENDATIONS ===\n"
        if removals > 0:
            fcm_text += "🚨 URGENT: User has had tokens removed\n"
            fcm_text += "• Check if user has reinstalled the app\n"
            fcm_text += "• Verify device connectivity\n"
            fcm_text += "• Consider reaching out to user for support\n"
        elif strikes >= 2:
            fcm_text += "⚠️ WARNING: User has multiple token strikes\n"
            fcm_text += "• Monitor for chronic delivery issues\n"
            fcm_text += "• Check notification frequency settings\n"
        elif strikes > 0:
            fcm_text += "ℹ️ INFO: User has occasional token issues\n"
            fcm_text += "• Normal for occasional network issues\n"
            fcm_text += "• Monitor for patterns\n"
        elif recent_events > 10:
            fcm_text += "📊 MONITORING: High recent event volume\n"
            fcm_text += "• Check for temporary network issues\n"
            fcm_text += "• Verify if issues are resolved\n"
        else:
            fcm_text += "✅ HEALTHY: No action required\n"
            fcm_text += "• User's token health is good\n"
            fcm_text += "• Continue normal monitoring\n"
        
        self.fcm_health_text.setText(fcm_text)

    def update_fcm_events_table(self, user_data):
        """Update the FCM events table for the selected user"""
        user_id = user_data['id']
        fcm_data = self.fcm_token_data.get(user_id, {})
        recent_events = fcm_data.get('recent_events', [])
        
        self.fcm_events_table.setRowCount(len(recent_events))
        
        for row, event in enumerate(recent_events):
            # Timestamp
            timestamp = event.get('timestamp', '')
            if timestamp:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.strftime('%m/%d %H:%M:%S')
                except:
                    pass
            self.fcm_events_table.setItem(row, 0, QTableWidgetItem(timestamp))
            
            # Event Type
            event_type = event.get('eventType', '')
            event_item = QTableWidgetItem(event_type)
            
            # Color code by event type
            if event_type == 'removal':
                event_item.setBackground(QBrush(QColor(255, 180, 180)))  # Light red
            elif event_type == 'strike':
                event_item.setBackground(QBrush(QColor(255, 220, 150)))  # Light orange
            elif event_type == 'error':
                event_item.setBackground(QBrush(QColor(255, 255, 180)))  # Light yellow
            
            self.fcm_events_table.setItem(row, 1, event_item)
            
            # Reason
            self.fcm_events_table.setItem(row, 2, QTableWidgetItem(event.get('reason', '')))
            
            # Context
            self.fcm_events_table.setItem(row, 3, QTableWidgetItem(event.get('context', '')))
            
            # Details
            details = event.get('details', {})
            if isinstance(details, dict):
                details_str = ', '.join([f"{k}={v}" for k, v in details.items()])
            else:
                details_str = str(details)
            self.fcm_events_table.setItem(row, 4, QTableWidgetItem(details_str[:100]))

    def export_fcm_health_report(self):
        """Export FCM health report for all users"""
        try:
            import json
            from datetime import datetime
            
            # Prepare export data
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_users': len(self.users_data),
                'users_with_token_issues': len([u for u in self.fcm_token_data.values() 
                                               if u.get('total_strikes', 0) > 0 or u.get('total_removals', 0) > 0]),
                'fcm_health_summary': {},
                'user_reports': []
            }
            
            # Add summary statistics
            if self.fcm_token_data:
                total_users = len(self.fcm_token_data)
                users_with_issues = len([data for data in self.fcm_token_data.values() 
                                        if data.get('total_strikes', 0) > 0 or data.get('total_removals', 0) > 0])
                users_with_strikes = len([data for data in self.fcm_token_data.values() 
                                         if data.get('total_strikes', 0) > 0])
                users_with_removals = len([data for data in self.fcm_token_data.values() 
                                          if data.get('total_removals', 0) > 0])
                
                export_data['fcm_health_summary'] = {
                    'total_users': total_users,
                    'users_with_issues': users_with_issues,
                    'users_with_strikes': users_with_strikes,
                    'users_with_removals': users_with_removals,
                    'health_percentage': ((total_users - users_with_issues) / total_users * 100) if total_users > 0 else 100
                }
            
            # Add individual user reports
            for user in self.users_data:
                user_id = user['id']
                fcm_data = self.fcm_token_data.get(user_id, {})
                
                user_report = {
                    'user_id': user_id,
                    'user_name': user.get('name', 'Unknown'),
                    'role': user.get('role', 'unknown'),
                    'is_likely_test': user.get('is_likely_test', False),
                    'engagement_score': user.get('engagement_score', 0),
                    'fcm_health': {
                        'recent_events_count': fcm_data.get('recent_events_count', 0),
                        'total_strikes': fcm_data.get('total_strikes', 0),
                        'total_removals': fcm_data.get('total_removals', 0),
                        'contexts': fcm_data.get('contexts', []),
                        'issues_count': len(fcm_data.get('issues', []))
                    }
                }
                
                # Add health status
                recent_events = fcm_data.get('recent_events_count', 0)
                strikes = fcm_data.get('total_strikes', 0)
                removals = fcm_data.get('total_removals', 0)
                
                if recent_events == 0 and strikes == 0 and removals == 0:
                    user_report['fcm_health']['status'] = 'healthy'
                elif removals > 0 or strikes >= 2:
                    user_report['fcm_health']['status'] = 'critical'
                elif strikes > 0 or recent_events > 5:
                    user_report['fcm_health']['status'] = 'warning'
                else:
                    user_report['fcm_health']['status'] = 'monitoring'
                
                export_data['user_reports'].append(user_report)
            
            # Save to file
            filename = f"danoggin_fcm_health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.status_text.append(f"📤 Exported FCM health report to {filename}")
            QMessageBox.information(self, "Export Complete", 
                                   f"FCM health report exported to {filename}\n\n"
                                   f"Report includes:\n"
                                   f"• {export_data['total_users']} total users\n"
                                   f"• {export_data['users_with_token_issues']} users with token issues\n"
                                   f"• Individual health reports for all users")
            
        except Exception as e:
            self.status_text.append(f"❌ Export error: {str(e)}")
            QMessageBox.critical(self, "Export Error", f"Failed to export FCM health report: {str(e)}")

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

        # Enhanced confirmation dialog with engagement info and FCM health
        is_test = user_data.get('is_likely_test', False)
        score = user_data.get('engagement_score', 0)
        fcm_data = self.fcm_token_data.get(user_id, {})

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

        # FCM health warning
        fcm_warning = ""
        strikes = fcm_data.get('total_strikes', 0)
        removals = fcm_data.get('total_removals', 0)
        recent_events = fcm_data.get('recent_events_count', 0)
        
        if strikes > 0 or removals > 0 or recent_events > 5:
            fcm_warning = f"\n\n🔔 FCM Token Health: {strikes} strikes, {removals} removals, {recent_events} recent events"

        # Confirmation dialog
        confirm = QMessageBox.question(
            self,
            "Confirm User Deletion",
            f"Are you sure you want to delete this user?\n\n"
            f"Name: {user_name}\n"
            f"ID: {user_id}\n"
            f"Role: {user_role}\n"
            f"Engagement Score: {score}{relationship_info}{test_warning}{fcm_warning}\n\n"
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