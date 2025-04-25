# # # # # # # # # # # # # # # # # # # # # # # # # # # 
#   BlueVista Solutions            
#   Company proprietary      Author: John Ivory
#   All rights reserved     Created: 4/25/2025, 9:15 AM
#   Copyright 2025
# # # # # # # # # # # # # # # # # # # # # # # # # # #

import os
import argparse
import json
from firebase_manager import FirebaseManager
from typing import Dict, List, Any, Tuple


class ImageMigrationTool:
    """Tool for migrating images to Firebase Storage"""

    def __init__(self, firebase: FirebaseManager):
        """Initialize the migration tool

        Args:
            firebase: Initialized FirebaseManager instance
        """
        self.firebase = firebase

    def migrate_pack(self, pack_id: str, assets_folder: str) -> Tuple[int, int]:
        """Migrate images for a specific question pack

        Args:
            pack_id: ID of the question pack to migrate
            assets_folder: Path to the Flutter assets folder containing images

        Returns:
            Tuple of (successful_uploads, failed_uploads)
        """
        # Get the question pack data
        packs = self.firebase.get_question_packs()
        pack = next((p for p in packs if p.get('id') == pack_id), None)

        if not pack:
            print(f"Error: Question pack with ID '{pack_id}' not found")
            return 0, 0

        print(f"Migrating images for pack: {pack.get('name')} (ID: {pack_id})")

        # Track migration stats
        success_count = 0
        failed_count = 0

        # Migrate images for each question
        questions = pack.get('questions', [])
        for i, question in enumerate(questions):
            # Migrate correct answer image
            correct_answer = question.get('correctAnswer', {})
            result = self._migrate_answer_option(
                pack_id,
                i,
                correct_answer,
                assets_folder,
                is_correct=True
            )

            if result:
                success_count += 1
                # Update the correct answer with the cloud URL
                question['correctAnswer'] = result
            else:
                failed_count += self._count_image_in_option(correct_answer)

            # Migrate decoy answers
            decoy_answers = question.get('decoyAnswers', [])
            for j, decoy in enumerate(decoy_answers):
                result = self._migrate_answer_option(
                    pack_id,
                    i,
                    decoy,
                    assets_folder,
                    decoy_index=j
                )

                if result:
                    success_count += 1
                    # Update the decoy with the cloud URL
                    decoy_answers[j] = result
                else:
                    failed_count += self._count_image_in_option(decoy)

        # Update the question pack in Firestore
        pack['imageFolder'] = f'question_packs/{pack_id}/images'
        success = self.firebase.update_question_pack(pack_id, pack)

        if success:
            print(f"✓ Updated question pack {pack_id} with new image URLs")
        else:
            print(f"✗ Failed to update question pack {pack_id}")

        return success_count, failed_count

    def _migrate_answer_option(
            self,
            pack_id: str,
            question_idx: int,
            option: Dict[str, Any],
            assets_folder: str,
            is_correct: bool = False,
            decoy_index: int = None
    ) -> Dict[str, Any]:
        """Migrate a single answer option's image to Firebase Storage

        Args:
            pack_id: Question pack ID
            question_idx: Index of the question in the pack
            option: Answer option dictionary
            assets_folder: Path to Flutter assets folder
            is_correct: Whether this is a correct answer
            decoy_index: Index of this decoy (None for correct answers)

        Returns:
            Updated option dictionary if successful, None otherwise
        """
        # Skip if no image path or already has URL
        image_path = option.get('imagePath')
        if not image_path or option.get('imageUrl'):
            return option

        # Convert Flutter asset path to local file path
        local_path = os.path.join(assets_folder, image_path.replace('assets/', ''))

        if not os.path.exists(local_path):
            print(f"✗ Image not found: {local_path}")
            return None

        # Generate cloud storage path
        file_ext = os.path.splitext(local_path)[1]
        answer_type = 'correct' if is_correct else f'decoy{decoy_index}'
        cloud_filename = f'q{question_idx}_{answer_type}{file_ext}'
        destination_path = f'question_packs/{pack_id}/images/{cloud_filename}'

        # Upload to Firebase Storage
        print(f"Uploading: {os.path.basename(local_path)} -> {destination_path}")
        url = self.firebase.upload_image(local_path, destination_path)

        if url:
            print(f"✓ Uploaded {os.path.basename(local_path)}")
            # Return updated option with cloud URL
            option['imageUrl'] = url
            return option
        else:
            print(f"✗ Failed to upload {os.path.basename(local_path)}")
            return None

    def _count_image_in_option(self, option: Dict[str, Any]) -> int:
        """Count if an option has an image (for statistics)"""
        return 1 if option.get('imagePath') else 0

    def migrate_all_packs(self, assets_folder: str) -> Tuple[int, int, int]:
        """Migrate images for all question packs

        Args:
            assets_folder: Path to the Flutter assets folder containing images

        Returns:
            Tuple of (packs_processed, successful_uploads, failed_uploads)
        """
        packs = self.firebase.get_question_packs()
        total_success = 0
        total_failed = 0

        print(f"Found {len(packs)} question packs to migrate")

        for pack in packs:
            pack_id = pack.get('id')
            success, failed = self.migrate_pack(pack_id, assets_folder)
            total_success += success
            total_failed += failed

        return len(packs), total_success, total_failed


def main():
    """Main function to run the migration tool"""
    parser = argparse.ArgumentParser(description="Danoggin Image Migration Tool")
    parser.add_argument("--service-account", required=True, help="Path to Firebase service account key file")
    parser.add_argument("--assets-folder", required=True, help="Path to Flutter assets folder")
    parser.add_argument("--pack-id", help="Specific question pack ID to migrate (optional)")

    args = parser.parse_args()

    # Initialize Firebase
    firebase = FirebaseManager(args.service_account)

    # Initialize migration tool
    migration_tool = ImageMigrationTool(firebase)

    # Run migration
    if args.pack_id:
        success, failed = migration_tool.migrate_pack(args.pack_id, args.assets_folder)
        print(f"\nMigration complete for pack {args.pack_id}")
        print(f"Successful uploads: {success}")
        print(f"Failed uploads: {failed}")
    else:
        packs, success, failed = migration_tool.migrate_all_packs(args.assets_folder)
        print(f"\nMigration complete for {packs} question packs")
        print(f"Successful uploads: {success}")
        print(f"Failed uploads: {failed}")


if __name__ == "__main__":
    main()