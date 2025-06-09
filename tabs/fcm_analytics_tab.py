# # # # # # # # # # # # # # # # # # # # # # # # # # # 
#   BlueVista Solutions            
#   Company proprietary      Author: John Ivory
#   All rights reserved     Created: 1/15/2025
#   Copyright 2025                                                                   
# # # # # # # # # # # # # # # # # # # # # # # # # # #
# tabs/fcm_analytics_tab.py

import os
import json
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGroupBox, QTextEdit, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView, QTabWidget, QComboBox,
                             QSpinBox, QProgressBar, QSplitter, QTreeWidget,
                             QTreeWidgetItem, QCheckBox, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QBrush, QPalette


class FCMAnalyticsTab(QWidget):
    """Comprehensive FCM token analytics and management tab"""

    def __init__(self, firebase_manager):
        super().__init__()
        self.firebase_manager = firebase_manager
        self.fcm_manager = firebase_manager.fcm
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.refresh_dashboard)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Top controls
        controls_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Refresh All")
        self.refresh_btn.clicked.connect(self.refresh_all_data)
        
        # Auto-refresh controls
        self.auto_refresh_checkbox = QCheckBox("Auto-refresh")
        self.auto_refresh_checkbox.stateChanged.connect(self.toggle_auto_refresh)
        
        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setRange(30, 300)
        self.refresh_interval_spin.setValue(60)
        self.refresh_interval_spin.setSuffix(" sec")
        
        controls_layout.addWidget(self.refresh_btn)
        controls_layout.addWidget(QLabel("Auto-refresh:"))
        controls_layout.addWidget(self.auto_refresh_checkbox)
        controls_layout.addWidget(self.refresh_interval_spin)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Main content in tabs
        self.main_tabs = QTabWidget()
        
        # Dashboard Tab
        self.dashboard_tab = self.create_dashboard_tab()
        self.main_tabs.addTab(self.dashboard_tab, "📊 Dashboard")
        
        # User Analysis Tab
        self.user_analysis_tab = self.create_user_analysis_tab()
        self.main_tabs.addTab(self.user_analysis_tab, "👥 User Analysis")
        
        # Token Events Tab
        self.events_tab = self.create_events_tab()
        self.main_tabs.addTab(self.events_tab, "📋 Token Events")
        
        # Trends Tab
        self.trends_tab = self.create_trends_tab()
        self.main_tabs.addTab(self.trends_tab, "📈 Trends")
        
        # Admin Tools Tab
        self.admin_tab = self.create_admin_tab()
        self.main_tabs.addTab(self.admin_tab, "🔧 Admin Tools")
        
        layout.addWidget(self.main_tabs)

        # Status area
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(80)
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.status_text)

        self.setLayout(layout)
        
        # Load initial data
        self.refresh_all_data()

    def create_dashboard_tab(self):
        """Create the main dashboard tab with system overview"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # System Health Overview
        health_group = QGroupBox("🩺 System Health Overview")
        health_layout = QVBoxLayout()
        
        # Health metrics display
        self.health_metrics_layout = QHBoxLayout()
        health_layout.addLayout(self.health_metrics_layout)
        
        # Progress bars for key metrics
        progress_layout = QHBoxLayout()
        
        self.health_progress = QProgressBar()
        self.health_progress.setRange(0, 100)
        self.health_progress.setFormat("Token Health: %p%")
        progress_layout.addWidget(self.health_progress)
        
        health_layout.addLayout(progress_layout)
        health_group.setLayout(health_layout)
        layout.addWidget(health_group)

        # Recent Activity Summary
        activity_group = QGroupBox("📊 Recent Activity (Last 7 Days)")
        activity_layout = QHBoxLayout()
        
        # Activity metrics cards
        self.activity_cards_layout = QHBoxLayout()
        activity_layout.addLayout(self.activity_cards_layout)
        
        activity_group.setLayout(activity_layout)
        layout.addWidget(activity_group)

        # Critical Alerts
        alerts_group = QGroupBox("🚨 Critical Alerts")
        alerts_layout = QVBoxLayout()
        
        self.alerts_text = QTextEdit()
        self.alerts_text.setMaximumHeight(120)
        self.alerts_text.setReadOnly(True)
        alerts_layout.addWidget(self.alerts_text)
        
        alerts_group.setLayout(alerts_layout)
        layout.addWidget(alerts_group)

        layout.addStretch()
        return tab

    def create_user_analysis_tab(self):
        """Create the user analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Time Period:"))
        self.user_analysis_days = QComboBox()
        self.user_analysis_days.addItems(["7 days", "14 days", "30 days"])
        self.user_analysis_days.currentTextChanged.connect(self.refresh_user_analysis)
        controls_layout.addWidget(self.user_analysis_days)
        
        self.export_users_btn = QPushButton("📤 Export User Data")
        self.export_users_btn.clicked.connect(self.export_user_token_data)
        controls_layout.addWidget(self.export_users_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Split between users list and details
        splitter = QSplitter(Qt.Horizontal)

        # Users with issues table
        users_widget = QWidget()
        users_layout = QVBoxLayout(users_widget)
        users_layout.addWidget(QLabel("Users with Token Issues:"))
        
        self.users_issues_table = QTableWidget()
        self.users_issues_table.setColumnCount(6)
        self.users_issues_table.setHorizontalHeaderLabels([
            "User ID", "Name", "Total Issues", "Removals", "Strikes", "Contexts"
        ])
        self.users_issues_table.horizontalHeader().setStretchLastSection(True)
        self.users_issues_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.users_issues_table.itemSelectionChanged.connect(self.on_user_selected)
        users_layout.addWidget(self.users_issues_table)
        
        splitter.addWidget(users_widget)

        # User details
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.addWidget(QLabel("User Token Health Report:"))
        
        self.user_details_text = QTextEdit()
        self.user_details_text.setReadOnly(True)
        details_layout.addWidget(self.user_details_text)
        
        # User actions
        user_actions_layout = QHBoxLayout()
        self.view_user_events_btn = QPushButton("View All Events")
        self.view_user_events_btn.clicked.connect(self.view_selected_user_events)
        self.view_user_events_btn.setEnabled(False)
        user_actions_layout.addWidget(self.view_user_events_btn)
        user_actions_layout.addStretch()
        details_layout.addLayout(user_actions_layout)
        
        splitter.addWidget(details_widget)
        
        layout.addWidget(splitter)
        return tab

    def create_events_tab(self):
        """Create the token events debugging tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Event filters
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Event Type:"))
        self.event_type_combo = QComboBox()
        self.event_type_combo.addItems(["All Events", "Errors", "Strikes", "Removals"])
        self.event_type_combo.currentTextChanged.connect(self.refresh_events)
        filters_layout.addWidget(self.event_type_combo)
        
        filters_layout.addWidget(QLabel("Days:"))
        self.events_days_spin = QSpinBox()
        self.events_days_spin.setRange(1, 30)
        self.events_days_spin.setValue(7)
        self.events_days_spin.valueChanged.connect(self.refresh_events)
        filters_layout.addWidget(self.events_days_spin)
        
        filters_layout.addWidget(QLabel("Max Events:"))
        self.events_limit_spin = QSpinBox()
        self.events_limit_spin.setRange(50, 1000)
        self.events_limit_spin.setValue(200)
        self.events_limit_spin.setSingleStep(50)
        filters_layout.addWidget(self.events_limit_spin)
        
        self.refresh_events_btn = QPushButton("🔄 Refresh Events")
        self.refresh_events_btn.clicked.connect(self.refresh_events)
        filters_layout.addWidget(self.refresh_events_btn)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)

        # Events table
        self.events_table = QTableWidget()
        self.events_table.setColumnCount(7)
        self.events_table.setHorizontalHeaderLabels([
            "Timestamp", "Event Type", "User ID", "User Name", "Reason", "Context", "Details"
        ])
        self.events_table.horizontalHeader().setStretchLastSection(True)
        self.events_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.events_table)

        return tab

    def create_trends_tab(self):
        """Create the trends analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Trends controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Analysis Period:"))
        self.trends_days_combo = QComboBox()
        self.trends_days_combo.addItems(["7 days", "14 days", "30 days", "60 days"])
        self.trends_days_combo.setCurrentText("30 days")
        self.trends_days_combo.currentTextChanged.connect(self.refresh_trends)
        controls_layout.addWidget(self.trends_days_combo)
        
        self.refresh_trends_btn = QPushButton("🔄 Refresh Trends")
        self.refresh_trends_btn.clicked.connect(self.refresh_trends)
        controls_layout.addWidget(self.refresh_trends_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Trends display
        trends_scroll = QScrollArea()
        trends_content = QWidget()
        self.trends_layout = QVBoxLayout(trends_content)
        
        # Trends will be populated dynamically
        self.trends_summary_text = QTextEdit()
        self.trends_summary_text.setReadOnly(True)
        self.trends_layout.addWidget(self.trends_summary_text)
        
        trends_scroll.setWidget(trends_content)
        trends_scroll.setWidgetResizable(True)
        layout.addWidget(trends_scroll)

        return tab

    def create_admin_tab(self):
        """Create the admin tools tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Cleanup Tools
        cleanup_group = QGroupBox("🧹 Cleanup Tools")
        cleanup_layout = QVBoxLayout()
        
        # Token events cleanup
        token_cleanup_layout = QHBoxLayout()
        token_cleanup_layout.addWidget(QLabel("Clean up token events older than:"))
        
        self.cleanup_days_spin = QSpinBox()
        self.cleanup_days_spin.setRange(7, 365)
        self.cleanup_days_spin.setValue(30)
        self.cleanup_days_spin.setSuffix(" days")
        token_cleanup_layout.addWidget(self.cleanup_days_spin)
        
        self.cleanup_events_btn = QPushButton("🗑️ Cleanup Old Events")
        self.cleanup_events_btn.clicked.connect(self.cleanup_old_events)
        self.cleanup_events_btn.setStyleSheet("background-color: #ffeeee;")
        token_cleanup_layout.addWidget(self.cleanup_events_btn)
        
        token_cleanup_layout.addStretch()
        cleanup_layout.addLayout(token_cleanup_layout)
        
        cleanup_group.setLayout(cleanup_layout)
        layout.addWidget(cleanup_group)

        # Export Tools
        export_group = QGroupBox("📤 Export Tools")
        export_layout = QVBoxLayout()
        
        export_buttons_layout = QHBoxLayout()
        
        self.export_summary_btn = QPushButton("📊 Export Summary Stats")
        self.export_summary_btn.clicked.connect(self.export_summary_stats)
        export_buttons_layout.addWidget(self.export_summary_btn)
        
        self.export_problem_users_btn = QPushButton("🚨 Export Problem Users")
        self.export_problem_users_btn.clicked.connect(self.export_problem_users)
        export_buttons_layout.addWidget(self.export_problem_users_btn)
        
        self.export_all_events_btn = QPushButton("📋 Export Recent Events")
        self.export_all_events_btn.clicked.connect(self.export_recent_events)
        export_buttons_layout.addWidget(self.export_all_events_btn)
        
        export_buttons_layout.addStretch()
        export_layout.addLayout(export_buttons_layout)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)

        # System Information
        system_group = QGroupBox("ℹ️ System Information")
        system_layout = QVBoxLayout()
        
        self.system_info_text = QTextEdit()
        self.system_info_text.setReadOnly(True)
        self.system_info_text.setMaximumHeight(200)
        system_layout.addWidget(self.system_info_text)
        
        system_group.setLayout(system_layout)
        layout.addWidget(system_group)

        layout.addStretch()
        return tab

    # === REFRESH METHODS ===

    def refresh_all_data(self):
        """Refresh all data across all tabs"""
        self.status_text.append("🔄 Refreshing all FCM analytics data...")
        try:
            self.refresh_dashboard()
            self.refresh_user_analysis()
            self.refresh_events()
            self.refresh_trends()
            self.refresh_admin_info()
            self.status_text.append("✅ All data refreshed successfully")
        except Exception as e:
            self.status_text.append(f"❌ Error refreshing data: {str(e)}")

    def refresh_dashboard(self):
        """Refresh the dashboard data"""
        try:
            # Get FCM summary stats
            stats = self.fcm_manager.get_fcm_summary_stats()
            
            # Update health progress bar
            latest_metric = stats.get('latest_daily_metric', {})
            system_summary = latest_metric.get('systemSummary', {})
            health_pct = float(system_summary.get('tokenHealthPercentage', 0))
            self.health_progress.setValue(int(health_pct))
            
            # Color code the progress bar
            if health_pct >= 95:
                self.health_progress.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
            elif health_pct >= 85:
                self.health_progress.setStyleSheet("QProgressBar::chunk { background-color: #FFC107; }")
            else:
                self.health_progress.setStyleSheet("QProgressBar::chunk { background-color: #F44336; }")

            # Update health metrics
            self.update_health_metrics(stats)
            
            # Update activity cards
            self.update_activity_cards(stats)
            
            # Update alerts
            self.update_critical_alerts(stats)
            
        except Exception as e:
            self.status_text.append(f"❌ Error refreshing dashboard: {str(e)}")

    def update_health_metrics(self, stats):
        """Update the health metrics display"""
        # Clear existing widgets
        for i in reversed(range(self.health_metrics_layout.count())): 
            self.health_metrics_layout.itemAt(i).widget().setParent(None)
        
        latest_metric = stats.get('latest_daily_metric', {})
        system_summary = latest_metric.get('systemSummary', {})
        
        metrics = [
            ("Total Users", system_summary.get('totalActiveUsers', 0)),
            ("Total Tokens", system_summary.get('totalTokens', 0)),
            ("Healthy Tokens", system_summary.get('healthyTokens', 0)),
            ("Tokens w/ Issues", system_summary.get('tokensWithStrikes', 0))
        ]
        
        for title, value in metrics:
            card = self.create_metric_card(title, str(value))
            self.health_metrics_layout.addWidget(card)

    def update_activity_cards(self, stats):
        """Update the activity cards display"""
        # Clear existing widgets
        for i in reversed(range(self.activity_cards_layout.count())): 
            self.activity_cards_layout.itemAt(i).widget().setParent(None)
        
        recent_events = stats.get('recent_events', {})
        event_types = stats.get('event_types', {})
        
        activities = [
            ("Events (24h)", recent_events.get('last_24h', 0)),
            ("Events (7d)", recent_events.get('last_7d', 0)),
            ("Errors", event_types.get('errors', 0)),
            ("Strikes", event_types.get('strikes', 0)),
            ("Removals", event_types.get('removals', 0)),
            ("Affected Users", stats.get('affected_users_7d', 0))
        ]
        
        for title, value in activities:
            color = "#F44336" if "Error" in title or "Strike" in title or "Removal" in title else "#2196F3"
            card = self.create_metric_card(title, str(value), color)
            self.activity_cards_layout.addWidget(card)

    def update_critical_alerts(self, stats):
        """Update the critical alerts display"""
        alerts = []
        
        recent_events = stats.get('recent_events', {})
        if recent_events.get('last_24h', 0) > 50:
            alerts.append(f"🚨 High event volume: {recent_events['last_24h']} events in last 24h")
        
        event_types = stats.get('event_types', {})
        if event_types.get('removals', 0) > 5:
            alerts.append(f"⚠️ High token removals: {event_types['removals']} in last 7 days")
        
        if stats.get('affected_users_7d', 0) > 10:
            alerts.append(f"👥 Many affected users: {stats['affected_users_7d']} users with issues")
        
        latest_metric = stats.get('latest_daily_metric', {})
        system_summary = latest_metric.get('systemSummary', {})
        health_pct = float(system_summary.get('tokenHealthPercentage', 100))
        if health_pct < 85:
            alerts.append(f"📉 Low system health: {health_pct:.1f}% token health")
        
        if not alerts:
            alerts.append("✅ No critical alerts - system operating normally")
        
        self.alerts_text.setText("\n".join(alerts))

    def create_metric_card(self, title, value, color="#2196F3"):
        """Create a metric display card"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet(f"QFrame {{ border: 2px solid {color}; border-radius: 5px; padding: 5px; }}")
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        layout.addWidget(value_label)
        
        return card

    def refresh_user_analysis(self):
        """Refresh the user analysis data"""
        try:
            days_text = self.user_analysis_days.currentText()
            days = int(days_text.split()[0])
            
            users_with_issues = self.fcm_manager.get_users_with_token_issues(days=days)
            
            self.users_issues_table.setRowCount(len(users_with_issues))
            
            for row, user in enumerate(users_with_issues):
                # User ID
                self.users_issues_table.setItem(row, 0, QTableWidgetItem(user.get('userId', '')))
                
                # User Name
                self.users_issues_table.setItem(row, 1, QTableWidgetItem(user.get('userName', 'Unknown')))
                
                # Total Issues
                total_issues = len(user.get('issues', []))
                self.users_issues_table.setItem(row, 2, QTableWidgetItem(str(total_issues)))
                
                # Removals
                removals = user.get('total_removals', 0)
                self.users_issues_table.setItem(row, 3, QTableWidgetItem(str(removals)))
                
                # Strikes
                strikes = user.get('total_strikes', 0)
                self.users_issues_table.setItem(row, 4, QTableWidgetItem(str(strikes)))
                
                # Contexts
                contexts = ', '.join(user.get('contexts', []))
                self.users_issues_table.setItem(row, 5, QTableWidgetItem(contexts))
            
            self.status_text.append(f"📊 Found {len(users_with_issues)} users with token issues")
            
        except Exception as e:
            self.status_text.append(f"❌ Error refreshing user analysis: {str(e)}")

    def refresh_events(self):
        """Refresh the token events data"""
        try:
            # Get filter values
            event_type_text = self.event_type_combo.currentText()
            days = self.events_days_spin.value()
            limit = self.events_limit_spin.value()
            
            # Map UI text to event types
            event_types = None
            if event_type_text == "Errors":
                event_types = ['error']
            elif event_type_text == "Strikes":
                event_types = ['strike']
            elif event_type_text == "Removals":
                event_types = ['removal']
            
            events = self.fcm_manager.get_recent_token_events(
                days=days, 
                event_types=event_types, 
                limit=limit
            )
            
            self.events_table.setRowCount(len(events))
            
            for row, event in enumerate(events):
                # Timestamp
                timestamp = event.get('timestamp', '')
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        timestamp = dt.strftime('%m/%d %H:%M:%S')
                    except:
                        pass
                self.events_table.setItem(row, 0, QTableWidgetItem(timestamp))
                
                # Event Type
                event_type = event.get('eventType', '')
                self.events_table.setItem(row, 1, QTableWidgetItem(event_type))
                
                # User ID
                user_id = event.get('userId', '')[:12] + "..." if len(event.get('userId', '')) > 15 else event.get('userId', '')
                self.events_table.setItem(row, 2, QTableWidgetItem(user_id))
                
                # User Name
                self.events_table.setItem(row, 3, QTableWidgetItem(event.get('userName', 'Unknown')))
                
                # Reason
                self.events_table.setItem(row, 4, QTableWidgetItem(event.get('reason', '')))
                
                # Context
                self.events_table.setItem(row, 5, QTableWidgetItem(event.get('context', '')))
                
                # Details
                details = event.get('details', {})
                if isinstance(details, dict):
                    details_str = ', '.join([f"{k}={v}" for k, v in details.items()])
                else:
                    details_str = str(details)
                self.events_table.setItem(row, 6, QTableWidgetItem(details_str[:50]))
            
            self.status_text.append(f"📋 Loaded {len(events)} token events")
            
        except Exception as e:
            self.status_text.append(f"❌ Error refreshing events: {str(e)}")

    def refresh_trends(self):
        """Refresh the trends analysis data"""
        try:
            days_text = self.trends_days_combo.currentText()
            days = int(days_text.split()[0])
            
            trends = self.fcm_manager.get_token_health_trends(days=days)
            
            # Format trends summary
            summary = trends.get('summary', {})
            trends_text = f"=== TOKEN HEALTH TRENDS ({days} days) ===\n\n"
            trends_text += f"Average Health Percentage: {summary.get('avg_health_percentage', 0):.1f}%\n"
            trends_text += f"Total Removals: {summary.get('total_removals_period', 0)}\n"
            trends_text += f"Total Errors: {summary.get('total_errors_period', 0)}\n"
            trends_text += f"Unique Affected Users: {summary.get('unique_affected_users', 0)}\n\n"
            
            # Daily breakdown
            dates = trends.get('dates', [])
            health_pcts = trends.get('token_health_percentages', [])
            removals = trends.get('total_removals', [])
            errors = trends.get('total_errors', [])
            
            trends_text += "=== DAILY BREAKDOWN ===\n"
            trends_text += "Date       | Health% | Removals | Errors\n"
            trends_text += "-" * 40 + "\n"
            
            for i, date in enumerate(dates[-10:]):  # Show last 10 days
                if i < len(health_pcts) and i < len(removals) and i < len(errors):
                    trends_text += f"{date} | {health_pcts[i]:6.1f}% | {removals[i]:8d} | {errors[i]:6d}\n"
            
            self.trends_summary_text.setText(trends_text)
            
        except Exception as e:
            self.status_text.append(f"❌ Error refreshing trends: {str(e)}")

    def refresh_admin_info(self):
        """Refresh the admin information"""
        try:
            stats = self.fcm_manager.get_fcm_summary_stats()
            
            info_text = "=== FCM SYSTEM INFORMATION ===\n\n"
            
            # Recent activity
            recent_events = stats.get('recent_events', {})
            info_text += f"Recent Activity:\n"
            info_text += f"• Last 24 hours: {recent_events.get('last_24h', 0)} events\n"
            info_text += f"• Last 7 days: {recent_events.get('last_7d', 0)} events\n"
            info_text += f"• Last 30 days: {recent_events.get('last_30d', 0)} events\n\n"
            
            # Top error reasons
            top_errors = stats.get('top_error_reasons', {})
            if top_errors:
                info_text += f"Top Error Reasons (7 days):\n"
                for reason, count in sorted(top_errors.items(), key=lambda x: x[1], reverse=True)[:5]:
                    info_text += f"• {reason}: {count} occurrences\n"
                info_text += "\n"
            
            # Latest system health
            latest_metric = stats.get('latest_daily_metric', {})
            if latest_metric:
                system_summary = latest_metric.get('systemSummary', {})
                info_text += f"Latest System Health:\n"
                info_text += f"• Total Active Users: {system_summary.get('totalActiveUsers', 0)}\n"
                info_text += f"• Total Tokens: {system_summary.get('totalTokens', 0)}\n"
                info_text += f"• Healthy Tokens: {system_summary.get('healthyTokens', 0)}\n"
                info_text += f"• Tokens with Issues: {system_summary.get('tokensWithStrikes', 0)}\n"
                info_text += f"• Health Percentage: {system_summary.get('tokenHealthPercentage', 0)}%\n"
            
            self.system_info_text.setText(info_text)
            
        except Exception as e:
            self.status_text.append(f"❌ Error refreshing admin info: {str(e)}")

    # === EVENT HANDLERS ===

    def toggle_auto_refresh(self, state):
        """Toggle auto-refresh functionality"""
        if state == Qt.Checked:
            interval = self.refresh_interval_spin.value() * 1000  # Convert to milliseconds
            self.auto_refresh_timer.start(interval)
            self.status_text.append(f"🔄 Auto-refresh enabled ({self.refresh_interval_spin.value()}s)")
        else:
            self.auto_refresh_timer.stop()
            self.status_text.append("⏸️ Auto-refresh disabled")

    def on_user_selected(self):
        """Handle user selection in the users table"""
        selected_rows = self.users_issues_table.selectedIndexes()
        if not selected_rows:
            self.view_user_events_btn.setEnabled(False)
            self.user_details_text.clear()
            return
        
        self.view_user_events_btn.setEnabled(True)
        
        # Get selected user ID
        row = selected_rows[0].row()
        user_id = self.users_issues_table.item(row, 0).text()
        
        # Get detailed user report
        try:
            report = self.fcm_manager.get_user_token_health_report(user_id)
            
            # Format the report
            details_text = f"=== TOKEN HEALTH REPORT ===\n"
            details_text += f"User ID: {report.get('user_id', 'Unknown')}\n\n"
            
            # Event summary
            summary = report.get('event_summary', {})
            details_text += f"Event Summary (30 days):\n"
            details_text += f"• Total Events: {summary.get('total_events', 0)}\n"
            details_text += f"• Errors: {summary.get('errors', 0)}\n"
            details_text += f"• Strikes: {summary.get('strikes', 0)}\n"
            details_text += f"• Removals: {summary.get('removals', 0)}\n\n"
            
            # Error patterns
            error_patterns = report.get('error_patterns', {})
            if error_patterns:
                details_text += f"Error Patterns:\n"
                for error, count in error_patterns.items():
                    details_text += f"• {error}: {count} times\n"
                details_text += "\n"
            
            # Contexts
            contexts = report.get('contexts', {})
            if contexts:
                details_text += f"Notification Contexts:\n"
                for context, count in contexts.items():
                    details_text += f"• {context}: {count} events\n"
                details_text += "\n"
            
            # Recommendations
            recommendations = report.get('recommendations', [])
            if recommendations:
                details_text += f"Recommendations:\n"
                for rec in recommendations:
                    details_text += f"• {rec}\n"
            
            self.user_details_text.setText(details_text)
            
        except Exception as e:
            self.user_details_text.setText(f"Error loading user report: {str(e)}")

    def view_selected_user_events(self):
        """View all events for the selected user"""
        selected_rows = self.users_issues_table.selectedIndexes()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        user_id = self.users_issues_table.item(row, 0).text()
        user_name = self.users_issues_table.item(row, 1).text()
        
        # Switch to events tab and filter by user
        self.main_tabs.setCurrentIndex(2)  # Events tab
        self.status_text.append(f"👤 Viewing events for user: {user_name} ({user_id})")
        
        # Note: In a full implementation, you'd add a user filter to the events tab

    # === EXPORT METHODS ===

    def export_user_token_data(self):
        """Export user token data to file"""
        try:
            days_text = self.user_analysis_days.currentText()
            days = int(days_text.split()[0])
            
            users_with_issues = self.fcm_manager.get_users_with_token_issues(days=days)
            
            if not users_with_issues:
                QMessageBox.information(self, "Export", "No users with token issues found to export")
                return
            
            # Create export data
            export_data = {
                'export_date': datetime.now().isoformat(),
                'analysis_period_days': days,
                'total_users_with_issues': len(users_with_issues),
                'users': users_with_issues
            }
            
            # Save to file
            filename = f"fcm_user_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.status_text.append(f"📤 Exported {len(users_with_issues)} users to {filename}")
            QMessageBox.information(self, "Export Complete", f"User data exported to {filename}")
            
        except Exception as e:
            self.status_text.append(f"❌ Export error: {str(e)}")
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")

    def export_summary_stats(self):
        """Export FCM summary statistics"""
        try:
            stats = self.fcm_manager.get_fcm_summary_stats()
            
            filename = f"fcm_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(stats, f, indent=2, default=str)
            
            self.status_text.append(f"📤 Exported summary stats to {filename}")
            QMessageBox.information(self, "Export Complete", f"Summary statistics exported to {filename}")
            
        except Exception as e:
            self.status_text.append(f"❌ Export error: {str(e)}")

    def export_problem_users(self):
        """Export list of users with chronic problems"""
        try:
            users_with_issues = self.fcm_manager.get_users_with_token_issues(days=7)
            
            # Filter for users with chronic issues (multiple problems)
            chronic_users = [user for user in users_with_issues 
                           if user.get('total_removals', 0) > 0 or user.get('total_strikes', 0) >= 2]
            
            if not chronic_users:
                QMessageBox.information(self, "Export", "No users with chronic issues found")
                return
            
            # Create simplified export for support team
            export_data = []
            for user in chronic_users:
                export_data.append({
                    'user_id': user.get('userId', ''),
                    'user_name': user.get('userName', 'Unknown'),
                    'total_removals': user.get('total_removals', 0),
                    'total_strikes': user.get('total_strikes', 0),
                    'contexts': user.get('contexts', []),
                    'support_priority': 'HIGH' if user.get('total_removals', 0) > 0 else 'MEDIUM'
                })
            
            filename = f"fcm_problem_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.status_text.append(f"📤 Exported {len(chronic_users)} problem users to {filename}")
            QMessageBox.information(self, "Export Complete", 
                                   f"Problem users exported to {filename}\n"
                                   f"Found {len(chronic_users)} users needing support attention")
            
        except Exception as e:
            self.status_text.append(f"❌ Export error: {str(e)}")

    def export_recent_events(self):
        """Export recent token events"""
        try:
            events = self.fcm_manager.get_recent_token_events(days=7, limit=1000)
            
            filename = f"fcm_recent_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(events, f, indent=2, default=str)
            
            self.status_text.append(f"📤 Exported {len(events)} recent events to {filename}")
            QMessageBox.information(self, "Export Complete", f"Recent events exported to {filename}")
            
        except Exception as e:
            self.status_text.append(f"❌ Export error: {str(e)}")

    # === ADMIN OPERATIONS ===

    def cleanup_old_events(self):
        """Clean up old token events"""
        days_to_keep = self.cleanup_days_spin.value()
        
        confirm = QMessageBox.question(
            self,
            "Confirm Cleanup",
            f"Are you sure you want to delete token events older than {days_to_keep} days?\n\n"
            f"This action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return
        
        try:
            self.status_text.append(f"🧹 Starting cleanup of events older than {days_to_keep} days...")
            
            success, message, deleted_count = self.fcm_manager.cleanup_old_token_events(days_to_keep)
            
            if success:
                self.status_text.append(f"✅ {message}")
                QMessageBox.information(self, "Cleanup Complete", 
                                       f"Successfully deleted {deleted_count} old token events")
            else:
                self.status_text.append(f"❌ {message}")
                QMessageBox.critical(self, "Cleanup Error", message)
                
        except Exception as e:
            error_msg = f"Error during cleanup: {str(e)}"
            self.status_text.append(f"❌ {error_msg}")
            QMessageBox.critical(self, "Cleanup Error", error_msg)