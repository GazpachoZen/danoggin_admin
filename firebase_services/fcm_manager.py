# firebase_services/fcm_manager.py

from datetime import datetime, timedelta


class FCMManager:
    """Manager for FCM token analytics and management operations"""

    def __init__(self, base_manager):
        self.base_manager = base_manager

    @property
    def db(self):
        """Get the Firestore database client from base manager"""
        return self.base_manager.db

    # === TOKEN EVENTS ANALYSIS ===

    def get_recent_token_events(self, days=7, event_types=None, limit=100):
        """Get recent token events for debugging and analysis
        
        Args:
            days: Number of days to look back
            event_types: List of event types to filter by ('error', 'strike', 'removal')
            limit: Maximum number of events to return
            
        Returns:
            List of token event dictionaries
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff_date.isoformat()
            
            query = self.db.collection('token_events')\
                .where('timestamp', '>=', cutoff_str)\
                .order_by('timestamp', direction='DESCENDING')\
                .limit(limit)
            
            events = []
            for doc in query.stream():
                event_data = doc.to_dict()
                event_data['id'] = doc.id
                
                # Filter by event type if specified
                if event_types is None or event_data.get('eventType') in event_types:
                    events.append(event_data)
            
            return events
            
        except Exception as e:
            print(f"Error getting recent token events: {e}")
            return []

    def get_token_events_for_user(self, user_id, days=30):
        """Get all token events for a specific user
        
        Args:
            user_id: User ID to get events for
            days: Number of days to look back
            
        Returns:
            List of token events for the user
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff_date.isoformat()
            
            events = self.db.collection('token_events')\
                .where('userId', '==', user_id)\
                .where('timestamp', '>=', cutoff_str)\
                .order_by('timestamp', direction='DESCENDING')\
                .stream()
            
            user_events = []
            for doc in events:
                event_data = doc.to_dict()
                event_data['id'] = doc.id
                user_events.append(event_data)
            
            return user_events
            
        except Exception as e:
            print(f"Error getting token events for user {user_id}: {e}")
            return []

    def get_error_patterns(self, days=7):
        """Analyze error patterns from recent token events
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with error pattern analysis
        """
        try:
            events = self.get_recent_token_events(days=days, event_types=['error', 'strike'])
            
            patterns = {
                'total_errors': 0,
                'total_strikes': 0,
                'error_by_reason': {},
                'error_by_context': {},
                'affected_users': set(),
                'users_by_error_count': {},
                'temporal_distribution': {}
            }
            
            for event in events:
                event_type = event.get('eventType')
                reason = event.get('reason', 'unknown')
                context = event.get('context', 'unknown')
                user_id = event.get('userId')
                timestamp = event.get('timestamp', '')
                
                if event_type == 'error':
                    patterns['total_errors'] += 1
                elif event_type == 'strike':
                    patterns['total_strikes'] += 1
                
                # Count by reason
                patterns['error_by_reason'][reason] = patterns['error_by_reason'].get(reason, 0) + 1
                
                # Count by context
                patterns['error_by_context'][context] = patterns['error_by_context'].get(context, 0) + 1
                
                # Track affected users
                if user_id:
                    patterns['affected_users'].add(user_id)
                    patterns['users_by_error_count'][user_id] = patterns['users_by_error_count'].get(user_id, 0) + 1
                
                # Temporal distribution (by day)
                if timestamp:
                    try:
                        event_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).date()
                        day_str = event_date.strftime('%Y-%m-%d')
                        patterns['temporal_distribution'][day_str] = patterns['temporal_distribution'].get(day_str, 0) + 1
                    except:
                        pass
            
            # Convert set to count
            patterns['affected_users'] = len(patterns['affected_users'])
            
            return patterns
            
        except Exception as e:
            print(f"Error analyzing error patterns: {e}")
            return {}

    # === DAILY METRICS ANALYSIS ===

    def get_daily_metrics(self, days=30):
        """Get daily metrics for the specified number of days
        
        Args:
            days: Number of days of metrics to retrieve
            
        Returns:
            List of daily metrics dictionaries
        """
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            metrics = []
            current_date = start_date
            
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                doc_id = f'token_metrics_{date_str}'
                
                doc = self.db.collection('daily_metrics').document(doc_id).get()
                if doc.exists:
                    metric_data = doc.to_dict()
                    metric_data['doc_id'] = doc_id
                    metrics.append(metric_data)
                
                current_date += timedelta(days=1)
            
            return sorted(metrics, key=lambda x: x.get('date', ''), reverse=True)
            
        except Exception as e:
            print(f"Error getting daily metrics: {e}")
            return []

    def get_token_health_trends(self, days=30):
        """Analyze token health trends over time
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        try:
            daily_metrics = self.get_daily_metrics(days)
            
            trends = {
                'dates': [],
                'token_health_percentages': [],
                'total_removals': [],
                'total_errors': [],
                'affected_users': [],
                'summary': {
                    'avg_health_percentage': 0,
                    'total_removals_period': 0,
                    'total_errors_period': 0,
                    'unique_affected_users': set()
                }
            }
            
            for metric in reversed(daily_metrics):  # Chronological order
                date = metric.get('date', '')
                trends['dates'].append(date)
                
                # System summary data
                system_summary = metric.get('systemSummary', {})
                health_pct = float(system_summary.get('tokenHealthPercentage', 0))
                trends['token_health_percentages'].append(health_pct)
                
                # Token removal data
                token_removals = metric.get('tokenRemovals', {})
                removals = token_removals.get('totalRemovals', 0)
                trends['total_removals'].append(removals)
                trends['summary']['total_removals_period'] += removals
                
                # Token error data
                token_errors = metric.get('tokenErrors', {})
                errors = token_errors.get('totalErrors', 0) + token_errors.get('totalStrikes', 0)
                trends['total_errors'].append(errors)
                trends['summary']['total_errors_period'] += errors
                
                # Affected users
                user_impact = metric.get('userImpact', {})
                affected = user_impact.get('usersWithTokenIssues', 0)
                trends['affected_users'].append(affected)
                
                # Collect unique affected users
                user_details = user_impact.get('userDetails', [])
                for user in user_details:
                    trends['summary']['unique_affected_users'].add(user.get('userId', ''))
            
            # Calculate averages
            if trends['token_health_percentages']:
                trends['summary']['avg_health_percentage'] = sum(trends['token_health_percentages']) / len(trends['token_health_percentages'])
            
            trends['summary']['unique_affected_users'] = len(trends['summary']['unique_affected_users'])
            
            return trends
            
        except Exception as e:
            print(f"Error analyzing token health trends: {e}")
            return {}

    # === USER IMPACT ANALYSIS ===

    def get_users_with_token_issues(self, days=7):
        """Get users who have had token issues recently
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of users with their token issue details
        """
        try:
            # Get recent daily metrics
            daily_metrics = self.get_daily_metrics(days)
            
            users_with_issues = {}
            
            for metric in daily_metrics:
                date = metric.get('date', '')
                
                # From token removals
                token_removals = metric.get('tokenRemovals', {})
                removal_users = token_removals.get('userDetails', [])
                for user in removal_users:
                    user_id = user.get('userId', '')
                    if user_id:
                        if user_id not in users_with_issues:
                            users_with_issues[user_id] = {
                                'userId': user_id,
                                'userName': user.get('userName', 'Unknown'),
                                'issues': [],
                                'total_removals': 0,
                                'total_strikes': 0,
                                'contexts': set()
                            }
                        
                        users_with_issues[user_id]['issues'].append({
                            'date': date,
                            'type': 'removal',
                            'reason': user.get('reason', ''),
                            'context': user.get('context', '')
                        })
                        users_with_issues[user_id]['total_removals'] += 1
                        users_with_issues[user_id]['contexts'].add(user.get('context', ''))
                
                # From user impact data
                user_impact = metric.get('userImpact', {})
                impact_users = user_impact.get('userDetails', [])
                for user in impact_users:
                    user_id = user.get('userId', '')
                    if user_id:
                        if user_id not in users_with_issues:
                            users_with_issues[user_id] = {
                                'userId': user_id,
                                'userName': user.get('userName', 'Unknown'),
                                'issues': [],
                                'total_removals': 0,
                                'total_strikes': 0,
                                'contexts': set()
                            }
                        
                        users_with_issues[user_id]['total_strikes'] = max(
                            users_with_issues[user_id]['total_strikes'],
                            user.get('totalStrikes', 0)
                        )
            
            # Convert contexts set to list for JSON serialization
            for user_data in users_with_issues.values():
                user_data['contexts'] = list(user_data['contexts'])
            
            return list(users_with_issues.values())
            
        except Exception as e:
            print(f"Error getting users with token issues: {e}")
            return []

    def get_user_token_health_report(self, user_id):
        """Get comprehensive token health report for a specific user
        
        Args:
            user_id: User ID to analyze
            
        Returns:
            Dictionary with comprehensive user token health data
        """
        try:
            report = {
                'user_id': user_id,
                'recent_events': [],
                'event_summary': {
                    'total_events': 0,
                    'errors': 0,
                    'strikes': 0,
                    'removals': 0
                },
                'error_patterns': {},
                'contexts': {},
                'recommendations': []
            }
            
            # Get recent events for this user
            events = self.get_token_events_for_user(user_id, days=30)
            report['recent_events'] = events
            report['event_summary']['total_events'] = len(events)
            
            for event in events:
                event_type = event.get('eventType', '')
                reason = event.get('reason', '')
                context = event.get('context', '')
                
                # Count by event type
                if event_type in report['event_summary']:
                    report['event_summary'][event_type] += 1
                
                # Track error patterns
                if reason:
                    report['error_patterns'][reason] = report['error_patterns'].get(reason, 0) + 1
                
                # Track contexts
                if context:
                    report['contexts'][context] = report['contexts'].get(context, 0) + 1
            
            # Generate recommendations
            if report['event_summary']['removals'] > 0:
                report['recommendations'].append("User has had tokens removed - check device connectivity")
            
            if report['event_summary']['strikes'] >= 2:
                report['recommendations'].append("User has multiple strikes - monitor for chronic issues")
            
            if 'messaging/invalid-registration-token' in report['error_patterns']:
                report['recommendations'].append("Invalid token errors detected - user may need to reinstall app")
            
            if not events:
                report['recommendations'].append("No recent token events - user appears healthy")
            
            return report
            
        except Exception as e:
            print(f"Error generating user token health report for {user_id}: {e}")
            return {}

    # === ADMINISTRATIVE OPERATIONS ===

    def cleanup_old_token_events(self, days_to_keep=30):
        """Clean up token events older than specified days
        
        Args:
            days_to_keep: Number of days of events to keep
            
        Returns:
            Tuple (success, message, deleted_count)
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_str = cutoff_date.isoformat()
            
            print(f"Cleaning up token events older than {cutoff_str}")
            
            # Query old events in batches
            batch_size = 500
            total_deleted = 0
            
            while True:
                old_events = self.db.collection('token_events')\
                    .where('timestamp', '<', cutoff_str)\
                    .limit(batch_size)\
                    .stream()
                
                old_events_list = list(old_events)
                if not old_events_list:
                    break
                
                # Delete in batch
                batch = self.db.batch()
                for doc in old_events_list:
                    batch.delete(doc.reference)
                batch.commit()
                
                total_deleted += len(old_events_list)
                print(f"Deleted {len(old_events_list)} old token events (total: {total_deleted})")
                
                if len(old_events_list) < batch_size:
                    break
            
            return True, f"Successfully deleted {total_deleted} old token events", total_deleted
            
        except Exception as e:
            return False, f"Error cleaning up old token events: {str(e)}", 0

    def get_fcm_summary_stats(self):
        """Get overall FCM system health statistics
        
        Returns:
            Dictionary with FCM system statistics
        """
        try:
            stats = {
                'recent_events': {
                    'last_24h': 0,
                    'last_7d': 0,
                    'last_30d': 0
                },
                'event_types': {
                    'errors': 0,
                    'strikes': 0,
                    'removals': 0
                },
                'top_error_reasons': {},
                'affected_users_7d': 0,
                'latest_daily_metric': {}
            }
            
            # Get recent events
            events_24h = self.get_recent_token_events(days=1, limit=1000)
            events_7d = self.get_recent_token_events(days=7, limit=5000)
            events_30d = self.get_recent_token_events(days=30, limit=10000)
            
            stats['recent_events']['last_24h'] = len(events_24h)
            stats['recent_events']['last_7d'] = len(events_7d)
            stats['recent_events']['last_30d'] = len(events_30d)
            
            # Analyze 7-day events
            affected_users = set()
            for event in events_7d:
                event_type = event.get('eventType', '')
                if event_type in stats['event_types']:
                    stats['event_types'][event_type] += 1
                
                reason = event.get('reason', '')
                if reason:
                    stats['top_error_reasons'][reason] = stats['top_error_reasons'].get(reason, 0) + 1
                
                user_id = event.get('userId')
                if user_id:
                    affected_users.add(user_id)
            
            stats['affected_users_7d'] = len(affected_users)
            
            # Get latest daily metric
            latest_metrics = self.get_daily_metrics(days=1)
            if latest_metrics:
                stats['latest_daily_metric'] = latest_metrics[0]
            
            return stats
            
        except Exception as e:
            print(f"Error getting FCM summary stats: {e}")
            return {}

    def export_user_token_data(self, user_ids=None, days=30):
        """Export token data for specified users or all users
        
        Args:
            user_ids: List of user IDs to export (None for all users)
            days: Number of days of data to include
            
        Returns:
            List of dictionaries with user token data
        """
        try:
            if user_ids is None:
                # Get all users who have had token events
                events = self.get_recent_token_events(days=days, limit=10000)
                user_ids = list(set([event.get('userId') for event in events if event.get('userId')]))
            
            export_data = []
            
            for user_id in user_ids:
                user_report = self.get_user_token_health_report(user_id)
                export_data.append(user_report)
            
            return export_data
            
        except Exception as e:
            print(f"Error exporting user token data: {e}")
            return []