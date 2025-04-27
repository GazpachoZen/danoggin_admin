# # # # # # # # # # # # # # # # # # # # # # # # # # # 
#   BlueVista Solutions            
#   Company proprietary      Author: John Ivory
#   All rights reserved     Created: 4/26/2025, 1:57 PM
#   Copyright 2023                                                                   
# # # # # # # # # # # # # # # # # # # # # # # # # # #
from google.cloud import storage
import os
import sys


def test_gcs_connection(service_account_path, bucket_name=None):
    """Test connection to Google Cloud Storage directly"""
    print("\n--- GOOGLE CLOUD STORAGE TEST ---\n")

    # Set credentials environment variable
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path

    try:
        # Create a storage client
        client = storage.Client()
        print("✓ Created GCS client successfully")

        # List available buckets
        print("\nAvailable buckets:")
        buckets = list(client.list_buckets())

        if not buckets:
            print("No buckets found! You need to create a bucket in your project.")
            return

        for b in buckets:
            print(f"- {b.name}")

        # If bucket_name not provided, use the first available bucket
        if not bucket_name and buckets:
            bucket_name = buckets[0].name
            print(f"\nUsing first available bucket: {bucket_name}")

        # Try to access the bucket
        if bucket_name:
            try:
                bucket = client.bucket(bucket_name)
                print(f"✓ Successfully accessed bucket: {bucket_name}")

                # List some files in the bucket
                print("\nListing files in bucket (max 5):")
                blobs = list(bucket.list_blobs(max_results=5))

                if not blobs:
                    print("No files found in bucket")

                    # Try to upload a test file
                    print("\nTrying to upload a test file...")
                    test_file_path = "test_upload.txt"
                    with open(test_file_path, "w") as f:
                        f.write("This is a test file for GCS upload")

                    blob = bucket.blob("test_upload.txt")
                    blob.upload_from_filename(test_file_path)
                    blob.make_public()

                    print(f"✓ Successfully uploaded test file. URL: {blob.public_url}")
                    os.remove(test_file_path)
                else:
                    for blob in blobs:
                        print(f"- {blob.name}")
            except Exception as e:
                print(f"ERROR accessing bucket {bucket_name}: {str(e)}")
    except Exception as e:
        print(f"ERROR with GCS client: {str(e)}")

    print("\n--- END GCS TEST ---")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python gcs_test.py path/to/serviceAccountKey.json [bucket_name]")
        sys.exit(1)

    service_account_path = sys.argv[1]
    bucket_name = sys.argv[2] if len(sys.argv) > 2 else None

    test_gcs_connection(service_account_path, bucket_name)