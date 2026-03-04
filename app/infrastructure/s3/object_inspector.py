from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class S3ObjectMetadata:
    exists: bool
    size_bytes: int | None = None
    etag: str | None = None


class S3ObjectInspector:
    def __init__(self, region: str) -> None:
        self.region = region

    def head_object(self, bucket: str, key: str) -> S3ObjectMetadata:
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError as exc:
            raise RuntimeError("boto3 is required for S3 object inspection") from exc

        client = boto3.client("s3", region_name=self.region)
        try:
            response = client.head_object(Bucket=bucket, Key=key)
        except ClientError as exc:
            error_code = str(exc.response.get("Error", {}).get("Code", ""))
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                return S3ObjectMetadata(exists=False)
            raise

        return S3ObjectMetadata(
            exists=True,
            size_bytes=response.get("ContentLength"),
            etag=response.get("ETag"),
        )
