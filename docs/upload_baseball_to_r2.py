"""
Streams docs/data/baseball/ from GitHub straight into R2, without ever
needing a local git clone -- fetches each file from
raw.githubusercontent.com and immediately uploads it to R2.

Scale warning: this is 338,927 individual files (mostly the boxscores
archive -- one JSON file per MLB game across history). Even parallelized,
expect this to take HOURS, not minutes. It's resumable -- if it gets
interrupted, just run it again and it'll skip everything already done.

Needs R2 API credentials as environment variables (never share these
directly in chat):
  R2_ACCOUNT_ID       - found in Cloudflare dashboard R2 overview
  R2_ACCESS_KEY_ID     ) both generated under
  R2_SECRET_ACCESS_KEY  ) R2 -> Manage R2 API Tokens -> Create API Token

Install:
  pip install boto3 requests

Run (needs baseball_manifest.txt in the same folder):
  export R2_ACCOUNT_ID=xxxx
  export R2_ACCESS_KEY_ID=xxxx
  export R2_SECRET_ACCESS_KEY=xxxx
  python3 upload_baseball_to_r2.py
"""

import mimetypes
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
import requests
from botocore.config import Config

BUCKET_NAME = "sporting-almanac-data"
R2_PREFIX = "baseball"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/NickJe77/nickje77.github.io/main/docs/data/baseball"
MANIFEST_FILE = "baseball_manifest.txt"
PROGRESS_FILE = "baseball_upload_progress.txt"
NUM_WORKERS = 12
MAX_RETRIES = 3


def get_client():
    account_id = os.environ.get("R2_ACCOUNT_ID")
    access_key = os.environ.get("R2_ACCESS_KEY_ID")
    secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")

    missing = [name for name, val in [
        ("R2_ACCOUNT_ID", account_id),
        ("R2_ACCESS_KEY_ID", access_key),
        ("R2_SECRET_ACCESS_KEY", secret_key),
    ] if not val]
    if missing:
        print(f"Missing environment variable(s): {', '.join(missing)}")
        sys.exit(1)

    endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4", max_pool_connections=NUM_WORKERS * 2),
        region_name="auto",
    )


def load_manifest():
    if not os.path.exists(MANIFEST_FILE):
        print(f"Could not find {MANIFEST_FILE} -- make sure it's in the same folder as this script.")
        sys.exit(1)
    with open(MANIFEST_FILE, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def load_completed():
    if not os.path.exists(PROGRESS_FILE):
        return set()
    with open(PROGRESS_FILE, encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def mark_completed(rel_path):
    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write(rel_path + "\n")


def transfer_one(client, session, rel_path):
    url = f"{GITHUB_RAW_BASE}/{rel_path}"
    r2_key = f"{R2_PREFIX}/{rel_path}"

    content_type, _ = mimetypes.guess_type(rel_path)
    extra_args = {"ContentType": content_type} if content_type else {}

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            client.put_object(
                Bucket=BUCKET_NAME, Key=r2_key, Body=resp.content, **extra_args
            )
            return rel_path, True, None
        except Exception as e:
            last_error = e
            time.sleep(2 * (attempt + 1))
    return rel_path, False, str(last_error)


def main():
    client = get_client()
    manifest = load_manifest()
    completed = load_completed()

    todo = [p for p in manifest if p not in completed]
    print(f"Manifest: {len(manifest)} file(s) total, {len(completed)} already done, {len(todo)} remaining.")

    if not todo:
        print("Nothing left to do.")
        return

    session = requests.Session()
    done_count = 0
    failed = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(transfer_one, client, session, p): p for p in todo}
        for future in as_completed(futures):
            rel_path, success, error = future.result()
            if success:
                mark_completed(rel_path)
                done_count += 1
            else:
                failed.append((rel_path, error))
                print(f"  FAILED: {rel_path} -- {error}")

            if done_count % 200 == 0 and done_count > 0:
                elapsed = time.time() - start_time
                rate = done_count / elapsed
                remaining = len(todo) - done_count
                eta_min = (remaining / rate) / 60 if rate > 0 else 0
                print(f"[{done_count}/{len(todo)}] {rate:.1f} files/sec, "
                      f"~{eta_min:.0f} min remaining")

    print(f"\nDone. {done_count} succeeded, {len(failed)} failed this run.")
    if failed:
        print("Failed files (re-run the script to retry these):")
        for rel_path, error in failed[:20]:
            print(f"  {rel_path}: {error}")
        if len(failed) > 20:
            print(f"  ... and {len(failed) - 20} more")


if __name__ == "__main__":
    main()
