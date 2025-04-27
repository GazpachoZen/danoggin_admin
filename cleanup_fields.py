# # # # # # # # # # # # # # # # # # # # # # # # # # # 
#   BlueVista Solutions            
#   Company proprietary      Author: John Ivory
#   All rights reserved     Created: 4/27/2025, 9:22 AM
#   Copyright 2023                                                                   
# # # # # # # # # # # # # # # # # # # # # # # # # # #
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import argparse


def cleanup_question_packs(service_account_path, pack_id=None):
    """
    Remove 'newly_uploaded' field from answer options in question packs

    Args:
        service_account_path: Path to Firebase service account key
        pack_id: Optional specific pack ID to clean (if None, cleans all packs)
    """
    # Initialize Firebase
    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    # Get reference to question_packs collection
    packs_ref = db.collection('question_packs')

    if pack_id:
        # Process only the specified pack
        packs = [packs_ref.document(pack_id).get()]
        if not packs[0].exists:
            print(f"Error: Question pack with ID '{pack_id}' not found")
            return
    else:
        # Process all packs
        packs = packs_ref.stream()

    total_cleaned = 0

    for pack_doc in packs:
        if not pack_doc.exists:
            continue

        pack_data = pack_doc.to_dict()
        pack_id = pack_doc.id
        modified = False

        print(f"Processing pack: {pack_data.get('name', 'Unnamed')} (ID: {pack_id})")

        # Process questions
        questions = pack_data.get('questions', [])
        for question in questions:
            # Clean correct answer
            correct_answer = question.get('correctAnswer', {})
            if 'newly_uploaded' in correct_answer:
                correct_answer.pop('newly_uploaded')
                modified = True
                total_cleaned += 1

            # Clean decoy answers
            decoy_answers = question.get('decoyAnswers', [])
            for decoy in decoy_answers:
                if 'newly_uploaded' in decoy:
                    decoy.pop('newly_uploaded')
                    modified = True
                    total_cleaned += 1

        # Update the document if modified
        if modified:
            packs_ref.document(pack_id).set(pack_data)
            print(f"✓ Updated pack {pack_id}, cleaned {total_cleaned} answer options")
        else:
            print(f"- No 'newly_uploaded' fields found in pack {pack_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up 'newly_uploaded' fields from question packs")
    parser.add_argument("--service-account", required=True, help="Path to Firebase service account key file")
    parser.add_argument("--pack-id", help="Specific question pack ID to clean (optional)")

    args = parser.parse_args()

    cleanup_question_packs(args.service_account, args.pack_id)
    print("Cleanup complete!")