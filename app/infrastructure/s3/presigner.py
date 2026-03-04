from __future__ import annotations


class S3Presigner:
    def __init__(self, region: str) -> None:
        self.region = region

    def generate_put_url(
        self,
        bucket: str,
        key: str,
        content_type: str,
        expires_seconds: int,
    ) -> str:
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required for presigned S3 URLs") from exc

        client = boto3.client("s3", region_name=self.region)
        return client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_seconds,
            HttpMethod="PUT",
        )
