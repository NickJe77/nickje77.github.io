"""
Re-syncs baseball/allstar.json from git to R2. The git-hosted file has
complete data (1946-2025, 79 years), but the R2 copy only has 2025 --
this fixes that specific gap directly rather than rebuilding anything.

Needs the same R2 secrets already configured in this repo:
  R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
"""

import json
import os
import sys

import boto3
import requests
from botocore.config import Config

BUCKET_NAME = "sporting-almanac-data"
R2_KEY = "baseball/allstar.json"
GIT_SOURCE = "https://raw.githubusercontent.com/NickJe77/nickje77.github.io/main/docs/data/baseball/allstar.json"


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
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def main():
    client = get_client()

    print(f"Fetching {GIT_SOURCE}...")
    resp = requests.get(GIT_SOURCE, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    years = sorted(data.keys())
    print(f"Git source has {len(years)} year(s): {years[0]}-{years[-1]}")

    body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    client.put_object(Bucket=BUCKET_NAME, Key=R2_KEY, Body=body, ContentType="application/json")

    print(f"Uploaded to R2: {R2_KEY} ({len(years)} year(s))")


if __name__ == "__main__":
    main()
