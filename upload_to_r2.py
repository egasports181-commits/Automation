import argparse
import csv
import os
from pathlib import Path

import boto3
from botocore.config import Config
from dotenv import load_dotenv

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v"}

def required(name):
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing environment variable: {name}")
    return value

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Upload schedule.csv and referenced videos to R2")
    parser.add_argument("--folder", required=True, help="Folder with schedule.csv and referenced videos")
    args = parser.parse_args()
    folder = Path(args.folder).expanduser().resolve()
    schedule = folder / "schedule.csv"
    if not schedule.is_file():
        raise SystemExit(f"Missing {schedule}")

    client = boto3.client(
        "s3",
        endpoint_url=required("R2_ENDPOINT_URL"),
        aws_access_key_id=required("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=required("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )
    bucket = required("R2_BUCKET")
    with schedule.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    filenames = sorted({(row.get("filename") or "").strip() for row in rows if (row.get("filename") or "").strip()})
    for name in filenames:
        if Path(name).name != name:
            raise SystemExit(f"Use a plain filename without folders in schedule.csv: {name}")
        video = folder / name
        if not video.is_file():
            raise SystemExit(f"Missing video referenced in CSV: {video}")
        if video.suffix.lower() not in VIDEO_EXTENSIONS:
            print(f"Warning: unusual video extension: {name}")
        mime = "video/mp4" if video.suffix.lower() == ".mp4" else "video/quicktime"
        print(f"Uploading {name} ({video.stat().st_size / (1024*1024):.1f} MB)")
        client.upload_file(str(video), bucket, name, ExtraArgs={"ContentType": mime})

    # Upload schedule last so the worker doesn't see a new row before its video exists.
    client.upload_file(str(schedule), bucket, "schedule.csv", ExtraArgs={"ContentType": "text/csv"})
    print("Upload complete. Add/update rows in schedule.csv then run this script again.")

if __name__ == "__main__":
    main()
