#!/usr/bin/env python
# pack_creator.py

import os
import argparse
import firebase_admin
from firebase_admin import credentials, firestore


def create_question_pack(service_account_path, pack_name):
    """
    Create a new question pack in Firestore.

    Args:
        service_account_path: Path to the Firebase service account JSON file
        pack_name: Name of the question pack to create (used as ID)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)

        # Get Firestore client
        db = firestore.client()

        # Format pack name for the display name (underscores to spaces, capitalize words)
        display_name = ' '.join(word.capitalize() for word in pack_name.split('_'))

        # Create pack data
        pack_data = {
            'name': display_name,
            'id': pack_name,
            'imageFolder': f'question_packs/{pack_name}/images',
            'questions': []  # Empty array to start with
        }

        # Add the pack to Firestore with pack_name as document ID
        db.collection('question_packs').document(pack_name).set(pack_data)

        print(f"Successfully created question pack:")
        print(f"  ID: {pack_name}")
        print(f"  Display name: {display_name}")
        print(f"  Image folder: {pack_data['imageFolder']}")
        print(f"  Questions: {len(pack_data['questions'])}")

        return True

    except Exception as e:
        print(f"Error creating question pack: {str(e)}")
        return False


def main():
    """Command-line interface for creating question packs"""
    parser = argparse.ArgumentParser(description="Create a new question pack in Firestore")
    parser.add_argument("--service-account", default="resources/danoggin_service_account.json",
                        help="Path to Firebase service account key file (default: resources/danoggin_service_account.json)")
    parser.add_argument("--pack-name", required=True,
                        help="Name of the question pack to create (will be used as ID)")

    args = parser.parse_args()

    # Validate that the service account file exists
    if not os.path.exists(args.service_account):
        print(f"Error: Service account file not found at {args.service_account}")
        return False

    # Create the question pack
    success = create_question_pack(args.service_account, args.pack_name)

    if success:
        print(f"\nQuestion pack '{args.pack_name}' created successfully!")
    else:
        print(f"\nFailed to create question pack '{args.pack_name}'.")


if __name__ == "__main__":
    main()