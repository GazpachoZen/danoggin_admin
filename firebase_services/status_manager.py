# firebase_services/status_manager.py


class StatusManager:
    """Manager for responder status and check-in operations"""

    def __init__(self, base_manager):
        self.base_manager = base_manager

    @property
    def db(self):
        """Get the Firestore database client from base manager"""
        return self.base_manager.db

    def get_responder_status_data(self):
        """Get all responder_status data with summarized check-in information

        Returns:
            List of dictionaries with responder status information
        """
        try:
            print("Starting to fetch responder_status data")

            # Get direct reference to the responder_status collection
            responder_status_ref = self.db.collection('responder_status')

            # Use get() instead of stream() to ensure all documents are retrieved
            all_docs = responder_status_ref.get()
            doc_list = list(all_docs)

            print(f"Found {len(doc_list)} documents in responder_status collection")
            if len(doc_list) == 0:
                print("WARNING: No documents found in responder_status collection!")
            else:
                # Print first few document IDs for debugging
                print("First few document IDs:")
                for i, doc in enumerate(doc_list[:5]):
                    print(f"- {doc.id}")
                    if i >= 4:
                        break

            result = []

            for doc in doc_list:
                responder_id = doc.id
                print(f"Processing responder ID: {responder_id}")

                try:
                    # Get check-ins subcollection
                    check_ins_ref = responder_status_ref.document(responder_id).collection('check_ins')

                    # Use get() instead of stream() to ensure all documents are retrieved
                    check_ins = check_ins_ref.get()
                    check_ins_list = list(check_ins)
                    check_ins_count = len(check_ins_list)

                    print(f"Found {check_ins_count} check-ins for responder {responder_id}")

                    # Get latest check-in if any exist
                    latest_check_in = "Never"
                    if check_ins_count > 0:
                        # Get latest by timestamp field
                        latest_docs = check_ins_ref.order_by('timestamp', direction='DESCENDING').limit(1).get()
                        latest_docs_list = list(latest_docs)
                        if latest_docs_list:
                            latest_data = latest_docs_list[0].to_dict()
                            print(f"Latest check-in data fields: {', '.join(latest_data.keys())}")
                            if 'timestamp' in latest_data:
                                latest_check_in = latest_data['timestamp']
                                print(f"Latest timestamp: {latest_check_in}")

                    # Add to result
                    result.append({
                        'id': responder_id,
                        'check_ins': check_ins_count,
                        'latest_check_in': latest_check_in
                    })

                except Exception as e:
                    print(f"Error processing check-ins for {responder_id}: {e}")
                    import traceback
                    print(traceback.format_exc())

                    # Still add the responder to the list, but with 0 check-ins
                    result.append({
                        'id': responder_id,
                        'check_ins': 0,
                        'latest_check_in': "Error: " + str(e)
                    })

            print(f"Successfully processed {len(result)} responder status records")
            return result

        except Exception as e:
            print(f"Error getting responder status data: {e}")
            import traceback
            print(traceback.format_exc())
            return []

    def get_responder_check_ins(self, responder_id, limit=20):
        """Get detailed check-in data for a specific responder

        Args:
            responder_id: ID of the responder
            limit: Maximum number of check-ins to retrieve

        Returns:
            List of check-in dictionaries
        """
        try:
            print(f"Fetching check-ins for responder ID: {responder_id}")

            # First verify the responder_status document exists
            doc_ref = self.db.collection('responder_status').document(responder_id)
            doc = doc_ref.get()

            if not doc.exists:
                print(f"Responder status document {responder_id} does not exist")
                return []

            # Query the check_ins subcollection
            check_ins_query = doc_ref.collection('check_ins') \
                .order_by('timestamp', direction='DESCENDING') \
                .limit(limit)

            docs = list(check_ins_query.stream())
            print(f"Found {len(docs)} check-in documents (limited to {limit})")

            result = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id  # Add document ID
                result.append(data)

            return result

        except Exception as e:
            print(f"Error getting check-ins for {responder_id}: {e}")
            import traceback
            print(traceback.format_exc())
            return []

    def purge_responder_status(self, responder_id):
        """Delete a responder_status document and all its check-ins

        Args:
            responder_id: ID of the responder status to purge

        Returns:
            Tuple (success, message)
        """
        try:
            print(f"Starting to purge responder status for ID: {responder_id}")

            # First, check if the responder_status document exists
            doc_ref = self.db.collection('responder_status').document(responder_id)
            doc = doc_ref.get()
            if not doc.exists:
                return False, f"Responder status for ID {responder_id} not found"

            # Get all check-ins for this responder
            print(f"Fetching check-ins subcollection")
            check_ins_ref = doc_ref.collection('check_ins')
            check_ins = list(check_ins_ref.stream())
            print(f"Found {len(check_ins)} check-in documents to delete")

            # Delete all check-in documents
            batch_size = 0
            batch = self.db.batch()

            for doc in check_ins:
                batch.delete(doc.reference)
                batch_size += 1

                # Firestore batch has a limit of 500 operations
                if batch_size >= 400:
                    print(f"Committing batch of {batch_size} deletions")
                    batch.commit()
                    batch = self.db.batch()
                    batch_size = 0

            # Commit any remaining operations
            if batch_size > 0:
                print(f"Committing final batch of {batch_size} deletions")
                batch.commit()

            # Delete the responder_status document itself
            print(f"Deleting responder_status document")
            doc_ref.delete()

            return True, f"Successfully purged responder status and {len(check_ins)} check-ins"

        except Exception as e:
            print(f"Error purging responder status: {e}")
            import traceback
            print(traceback.format_exc())
            return False, f"Error purging responder status: {str(e)}"