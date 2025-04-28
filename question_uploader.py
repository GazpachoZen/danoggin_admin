# # # # # # # # # # # # # # # # # # # # # # # # # # # 
#   BlueVista Solutions            
#   Company proprietary      Author: John Ivory
#   All rights reserved     Created: 4/28/2025, 9:09 AM
#   Copyright 2025
# # # # # # # # # # # # # # # # # # # # # # # # # # #
# !/usr/bin/env python
# question_uploader.py

import os
import json
import argparse
import firebase_admin
from firebase_admin import credentials, firestore


def upload_questions(service_account_path, pack_name, json_file_path):
    """
    Upload questions from a JSON file to a specified question pack in Firestore.

    Args:
        service_account_path: Path to the Firebase service account JSON file
        pack_name: Name of the question pack to update
        json_file_path: Path to the JSON file containing questions to upload

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

        # Get reference to the question pack
        pack_ref = db.collection('question_packs').document(pack_name)
        doc = pack_ref.get()

        if not doc.exists:
            print(f"Error: Question pack '{pack_name}' does not exist!")
            return False

        # Get current pack data
        current_data = doc.to_dict()

        # Read and parse the JSON file
        with open(json_file_path, 'r') as file:
            questions_data = json.load(file)

        # Validate questions_data format
        if not isinstance(questions_data, list):
            print("Error: JSON file must contain a list of question objects")
            return False

        # Combine current questions with new questions
        combined_questions = current_data.get('questions', []) + questions_data

        # Update the question pack
        pack_ref.update({
            'questions': combined_questions
        })

        print(f"Successfully updated question pack '{pack_name}':")
        print(f"  Previous question count: {len(current_data.get('questions', []))}")
        print(f"  New questions added: {len(questions_data)}")
        print(f"  Total questions now: {len(combined_questions)}")

        return True

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in {json_file_path}: {str(e)}")
        return False
    except Exception as e:
        print(f"Error uploading questions: {str(e)}")
        return False


def main():
    """Command-line interface for uploading questions to Firestore"""
    parser = argparse.ArgumentParser(description="Upload questions to a Firestore question pack")
    parser.add_argument("--service-account", default="resources/danoggin_service_account.json",
                        help="Path to Firebase service account key file (default: resources/danoggin_service_account.json)")
    parser.add_argument("--pack-name", required=True,
                        help="Name of the question pack to update")
    parser.add_argument("--json-file", required=True,
                        help="Path to JSON file containing questions to upload")

    args = parser.parse_args()

    # Validate that the service account file exists
    if not os.path.exists(args.service_account):
        print(f"Error: Service account file not found at {args.service_account}")
        return False

    # Validate that the JSON file exists
    if not os.path.exists(args.json_file):
        print(f"Error: JSON file not found at {args.json_file}")
        return False

    # Upload the questions
    success = upload_questions(args.service_account, args.pack_name, args.json_file)

    if success:
        print(f"\nQuestions uploaded successfully to '{args.pack_name}'!")
    else:
        print(f"\nFailed to upload questions to '{args.pack_name}'.")


if __name__ == "__main__":
    main()