import os
import argparse
import sys
from firebase_manager import FirebaseManager
from image_migration_tool import ImageMigrationTool


def main():
    """Main function for the Danoggin Admin CLI tool"""
    parser = argparse.ArgumentParser(description="Danoggin Admin CLI")
    parser.add_argument("--service-account", required=True, help="Path to Firebase service account key file")
    parser.add_argument("--bucket",
                        help="Firebase Storage bucket name (optional, will try to determine from service account)")

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Migrate images command
    migrate_parser = subparsers.add_parser("migrate", help="Migrate images to Firebase Storage")
    migrate_parser.add_argument("--assets-folder", required=True, help="Path to Flutter assets folder")
    migrate_parser.add_argument("--pack-id", help="Specific question pack ID to migrate (optional)")

    # List question packs command
    list_parser = subparsers.add_parser("list", help="List question packs")

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize Firebase
    try:
        firebase = FirebaseManager(args.service_account, args.bucket)
    except Exception as e:
        print(f"Error initializing Firebase: {str(e)}")
        sys.exit(1)

    # Execute requested command
    if args.command == "migrate":
        migration_tool = ImageMigrationTool(firebase)

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

    elif args.command == "list":
        packs = firebase.get_question_packs()
        print(f"Found {len(packs)} question packs:")
        for pack in packs:
            print(f"- {pack.get('name', 'Unnamed')} (ID: {pack.get('id', 'Unknown')})")
            print(f"  Questions: {len(pack.get('questions', []))}")
            print()


if __name__ == "__main__":
    main()# danoggin_admin.py
import os
import argparse
import sys
import time
from firebase_manager import FirebaseManager
from image_migration_tool import ImageMigrationTool

def main():
    """Main function for the Danoggin Admin CLI tool"""
    parser = argparse.ArgumentParser(description="Danoggin Admin CLI")
    parser.add_argument("--service-account", required=True, help="Path to Firebase service account key file")
    parser.add_argument("--bucket", help="Cloud Storage bucket name (optional, will try to determine automatically)")

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Migrate images command
    migrate_parser = subparsers.add_parser("migrate", help="Migrate images to Cloud Storage")
    migrate_parser.add_argument("--assets-folder", required=True, help="Path to Flutter assets folder")
    migrate_parser.add_argument("--pack-id", help="Specific question pack ID to migrate (optional)")

    # List question packs command
    list_parser = subparsers.add_parser("list", help="List question packs")

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize Firebase
    try:
        firebase = FirebaseManager(args.service_account, args.bucket)
    except Exception as e:
        print(f"Error initializing Firebase: {str(e)}")
        sys.exit(1)

    # Execute requested command
    if args.command == "migrate":
        migration_tool = ImageMigrationTool(firebase)

        # Add a small delay to ensure all connections are established
        print("Preparing for migration...")
        time.sleep(1)

        if args.pack_id:
            # Normalize path for consistency
            assets_folder = os.path.normpath(args.assets_folder)
            success, failed = migration_tool.migrate_pack(args.pack_id, assets_folder)
            print(f"\nMigration complete for pack {args.pack_id}")
            print(f"Successful uploads: {success}")
            print(f"Failed uploads: {failed}")
        else:
            # Normalize path for consistency
            assets_folder = os.path.normpath(args.assets_folder)
            packs, success, failed = migration_tool.migrate_all_packs(assets_folder)
            print(f"\nMigration complete for {packs} question packs")
            print(f"Successful uploads: {success}")
            print(f"Failed uploads: {failed}")

    elif args.command == "list":
        packs = firebase.get_question_packs()
        print(f"Found {len(packs)} question packs:")
        for pack in packs:
            print(f"- {pack.get('name', 'Unnamed')} (ID: {pack.get('id', 'Unknown')})")
            print(f"  Questions: {len(pack.get('questions', []))}")
            print()

if __name__ == "__main__":
    main()