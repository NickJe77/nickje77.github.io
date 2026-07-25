"""
Uploads docs/data/baseball/ to R2. Meant to run inside a GitHub Actions
workflow AFTER actions/checkout, so every file is already sitting
locally on the runner -- no fetching from GitHub needed at all, just a
local file walk + upload, same pattern as basketball-nba-full-scraper.yml.

Uses the same secret names already configured in this repo:
  R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
"""

import mimetypes
import os
import sys

import boto3
from botocore.config import Config

BUCKET_NAME = "sporting-almanac-data"
LOCAL_ROOT = "docs/data/baseball"
R2_PREFIX = "baseball"


def get_client():
    endpoint = os.environ.get("R2_ENDPOINT")
    access_key = os.environ.get("R2_ACCESS_KEY_ID")
    secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")

    missing = [name for name, val in [
        ("R2_ENDPOINT", endpoint),
        ("R2_ACCESS_KEY_ID", access_key),
        ("R2_SECRET_ACCESS_KEY", secret_key),
    ] if not val]
    if missing:
        print(f"Missing environment variable(s): {', '.join(missing)}")
        sys.exit(1)

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4", max_pool_connections=20),
        region_name="auto",
    )


def main():
    if not os.path.isdir(LOCAL_ROOT):
        print(f"Could not find {LOCAL_ROOT} -- this must run after actions/checkout, from the repo root.")
        sys.exit(1)

    client = get_client()

    all_files = []
    for dirpath, _, filenames in os.walk(LOCAL_ROOT):
        for fname in filenames:
            if fname == ".DS_Store":
                continue
            all_files.append(os.path.join(dirpath, fname))

    print(f"Found {len(all_files)} file(s) under {LOCAL_ROOT}.")

    failed = []
    for i, local_path in enumerate(all_files, 1):
        rel_path = os.path.relpath(local_path, LOCAL_ROOT)
        r2_key = f"{R2_PREFIX}/{rel_path}".replace(os.sep, "/")

        content_type, _ = mimetypes.guess_type(local_path)
        extra_args = {"ContentType": content_type} if content_type else {}

        try:
            client.upload_file(local_path, BUCKET_NAME, r2_key, ExtraArgs=extra_args)
        except Exception as e:
            failed.append((rel_path, str(e)))
            print(f"  FAILED: {rel_path} -- {e}")

        if i % 1000 == 0:
            print(f"[{i}/{len(all_files)}] uploaded")

    print(f"\nDone. {len(all_files) - len(failed)} succeeded, {len(failed)} failed.")
    if failed:
        for rel_path, err in failed[:20]:
            print(f"  {rel_path}: {err}")


if __name__ == "__main__":
    main()
