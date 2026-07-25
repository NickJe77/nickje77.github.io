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


def get_existing_keys(client):
    """Lists every key already in R2 under the baseball/ prefix, so a
    re-run after a timeout skips everything already uploaded instead of
    starting over from scratch. One paginated list call covers this in
    ~340 requests total (1000 keys per page) rather than one HEAD
    request per file."""
    existing = set()
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=f"{R2_PREFIX}/"):
        for obj in page.get("Contents", []):
            existing.add(obj["Key"])
    return existing


def main():
    if not os.path.isdir(LOCAL_ROOT):
        print(f"Could not find {LOCAL_ROOT} -- this must run after actions/checkout, from the repo root.")
        sys.exit(1)

    client = get_client()

    print("Checking R2 for files already uploaded (so a re-run after a timeout resumes instead of restarting)...")
    existing_keys = get_existing_keys(client)
    print(f"Found {len(existing_keys)} file(s) already in R2.")

    all_files = []
    for dirpath, _, filenames in os.walk(LOCAL_ROOT):
        for fname in filenames:
            if fname == ".DS_Store":
                continue
            all_files.append(os.path.join(dirpath, fname))

    print(f"Found {len(all_files)} file(s) under {LOCAL_ROOT}.")

    todo = []
    for local_path in all_files:
        rel_path = os.path.relpath(local_path, LOCAL_ROOT)
        r2_key = f"{R2_PREFIX}/{rel_path}".replace(os.sep, "/")
        if r2_key not in existing_keys:
            todo.append((local_path, rel_path, r2_key))

    print(f"{len(all_files) - len(todo)} already uploaded, {len(todo)} remaining this run.")

    if not todo:
        print("Nothing left to do.")
        return

    failed = []
    for i, (local_path, rel_path, r2_key) in enumerate(todo, 1):
        content_type, _ = mimetypes.guess_type(local_path)
        extra_args = {"ContentType": content_type} if content_type else {}

        try:
            client.upload_file(local_path, BUCKET_NAME, r2_key, ExtraArgs=extra_args)
        except Exception as e:
            failed.append((rel_path, str(e)))
            print(f"  FAILED: {rel_path} -- {e}")

        if i % 1000 == 0:
            print(f"[{i}/{len(todo)}] uploaded")

    print(f"\nDone. {len(todo) - len(failed)} succeeded, {len(failed)} failed.")
    if failed:
        for rel_path, err in failed[:20]:
            print(f"  {rel_path}: {err}")


if __name__ == "__main__":
    main()
