# image_migration_tool.py
import os
import pathlib
from firebase_manager import FirebaseManager
from typing import Dict, List, Any, Tuple, Set


class ImageMigrationTool:
    """Tool for migrating images to Cloud Storage"""

    def __init__(self, firebase: FirebaseManager):
        """Initialize the migration tool

        Args:
            firebase: Initialized FirebaseManager instance
        """
        self.firebase = firebase
        # Cache to track already uploaded files
        self.uploaded_files_cache = {}

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
        # Track already processed image paths to avoid duplicates
        processed_images = set()

        # Migrate images for each question
        questions = pack.get('questions', [])
        for i, question in enumerate(questions):
            # Migrate correct answer image
            correct_answer = question.get('correctAnswer', {})
            result = self._migrate_answer_option(
                pack_id,
                correct_answer,
                assets_folder,
                processed_images
            )

            if result:
                if result.get('newly_uploaded', False):
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
                    decoy,
                    assets_folder,
                    processed_images
                )

                if result:
                    if result.get('newly_uploaded', False):
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
            option: Dict[str, Any],
            assets_folder: str,
            processed_images: Set[str]
    ) -> Dict[str, Any]:
        """Migrate a single answer option's image to Cloud Storage

        Args:
            pack_id: Question pack ID
            option: Answer option dictionary
            assets_folder: Path to Flutter assets folder
            processed_images: Set of already processed image paths

        Returns:
            Updated option dictionary if successful, None otherwise
        """
        # Skip if no image path or already has URL
        image_path = option.get('imagePath')
        if not image_path:
            return option

        # If this option already has an imageUrl, just return it
        if option.get('imageUrl'):
            return option

        # Check if we've already processed this image path
        if image_path in processed_images:
            # Return cached result
            cached_url = self.uploaded_files_cache.get(image_path)
            if cached_url:
                print(f"✓ Using previously uploaded image for {image_path}: {cached_url}")
                result = option.copy()
                result['imageUrl'] = cached_url
                # Mark as not newly uploaded since we're reusing
                result['newly_uploaded'] = False
                return result

        # Convert Flutter asset path to local file path
        local_path = os.path.join(assets_folder, image_path.replace('assets/', ''))
        local_path = local_path.replace('\\', '/')  # Normalize path separators

        if not os.path.exists(local_path):
            print(f"✗ Image not found: {local_path}")
            return None

        # Extract original filename
        filename = os.path.basename(local_path)

        # Generate cloud storage path preserving original filename
        destination_path = f'question_packs/{pack_id}/images/{filename}'

        # Check if file already exists in storage
        if self.firebase.check_blob_exists(destination_path):
            print(f"File already exists in storage: {destination_path}")
            # Get the URL and update the option
            url = f"https://storage.googleapis.com/{self.firebase.bucket.name}/{destination_path}"
            self.uploaded_files_cache[image_path] = url
            result = option.copy()
            result['imageUrl'] = url
            # Mark as not newly uploaded since it already existed
            result['newly_uploaded'] = False
            processed_images.add(image_path)
            return result

        # Upload to Cloud Storage
        print(f"Uploading: {filename} -> {destination_path}")
        url = self.firebase.upload_image(local_path, destination_path)

        if url:
            print(f"✓ Uploaded {filename}")
            # Cache the result
            self.uploaded_files_cache[image_path] = url
            processed_images.add(image_path)
            # Return updated option with cloud URL
            result = option.copy()
            result['imageUrl'] = url
            # Mark as newly uploaded for counting
            result['newly_uploaded'] = True
            return result
        else:
            print(f"✗ Failed to upload {filename}")
            return None

    def _count_image_in_option(self, option: Dict[str, Any]) -> int:
        """Count if an option has an image (for statistics)"""
        return 1 if option.get('imagePath') and not option.get('imageUrl') else 0

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