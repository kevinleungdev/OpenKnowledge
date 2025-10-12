from abc import ABC, abstractmethod

import logging
import os
import re
import shutil
from typing import BinaryIO, Dict, Tuple

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

from open_knowledge.constants import ERROR_MESSAGES
from open_knowledge.env import (
    S3_ACCESS_KEY_ID,
    S3_BUCKET_NAME,
    S3_ENABLE_TAGGING, 
    S3_ENDPOINT_URL,
    S3_KEY_PREFIX, 
    S3_REGION_NAME, 
    S3_SECRET_ACCESS_KEY,
    STORAGE_PROVIDER,
    UPLOAD_DIR, 
    SRC_LOG_LEVELS,
) 

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])


class StorageProvider(ABC):

    @abstractmethod
    def get_file(self, file_path: str) -> str:
        pass

    @abstractmethod
    def upload_file(self, file: BinaryIO, filename: str, tags: Dict[str, str]) -> Tuple[bytes, str]:
        pass

    @abstractmethod
    def delete_all_files(self) -> None:
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> None:
        pass


class LoacalStorageProvider(StorageProvider):

    def upload_file(
        self, file: BinaryIO, filename: str, tags: Dict[str, str]
    ) -> Tuple[bytes, str]:
        contents = file.read()
        if not contents:
            raise ValueError(ERROR_MESSAGES.EMPTY_CONTENT)
        
        file_path = f"{UPLOAD_DIR}/{filename}"
        with open(file_path, "wb") as f:
            f.write(contents)

        return contents, file_path

    def get_file(self, file_path: str) -> str:
        """Handles downloading of the file from the local storage"""
        return file_path

    def delete_file(self, file_path: str) -> None:
        """Handles deletion of a file from local storage."""
        filename = file_path.split("/")[-1]
        file_path = f"{UPLOAD_DIR}/{filename}"

        if os.path.isfile(file_path):
            os.remove(file_path)
        else:
            log.warning(f"File {file_path} not found in local storage.")

    def delete_all_files(self) -> None:
        """Handles deletion of all files from local storage."""
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    log.error(f"Failed to delete {file_path}. Reason: {e}")
        else:
            log.warning(f"Directory {UPLOAD_DIR} not found in local storage.")


class S3StorageProvider(StorageProvider):

    def __init__(self) -> None:
        config = Config(
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        )

        # If access key and secret are provided, use them to authenticate
        if S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY:
            self.s3_client = boto3.client(
                "s3", 
                endpoint_url=S3_ENDPOINT_URL,
                aws_access_key_id=S3_ACCESS_KEY_ID,
                aws_secret_access_key=S3_SECRET_ACCESS_KEY,
                region_name=S3_REGION_NAME,
                config=config
            )
        else:
            # If no explicit credentials are provided, fall back to default credentials
            self.s3_client = boto3.client(
                "s3", 
                endpoint_url=S3_ENDPOINT_URL,
                region_name=S3_REGION_NAME,
                config=config
            )

        self.bucket_name = S3_BUCKET_NAME
        self.key_prefix = S3_KEY_PREFIX if S3_KEY_PREFIX else ""

        self.local_storage = LoacalStorageProvider()


    @staticmethod
    def sanitize_tag_value(s: str) -> str:
        """Only include S3 allowed characters."""
        return re.sub(r"[^a-zA-Z0-9 äöüÄÖÜß\+\-=\._:/@]", "", s)


    def upload_file(
        self, file: BinaryIO, filename: str, tags: Dict[str, str]
    ) -> Tuple[bytes, str]:
        """Handles uploading of the file to s3 storage"""
        _, file_path = self.local_storage.upload_file(file, filename, tags)
        s3_key = os.path.join(self.key_prefix, filename)
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, s3_key)

            if S3_ENABLE_TAGGING and tags:
                sanitized_tags = {
                    self.sanitize_tag_value(k): self.sanitize_tag_value(v)
                    for k, v in tags.items()
                }
                tagging = {
                    "TagSet": [
                        {"Key": k, "Value": v} for k, v in sanitized_tags.items()
                    ]
                }
                self.s3_client.put_object_tagging(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Tagging=tagging,
                )
            
            return (
                open(file_path, "rb").read(), 
                f"s3://{self.bucket_name}/{s3_key}"
            )
        except ClientError as e:
            raise RuntimeError(f"Error uploading file to S3. Reason: {e}")


    def get_file(self, file_path: str) -> str:
        """Handles downloading of the file from s3 storage"""
        try:
            s3_key = self._extract_s3_key(file_path)
            local_file_path = self._get_local_file_path(s3_key)
            
            self.s3_client.download_file(self.bucket_name, s3_key, local_file_path)
            return local_file_path
        except ClientError as e:
            raise RuntimeError(f"Error downloading file from S3. Reason: {e}")


    def delete_file(self, file_path: str) -> None:
        """Handles deletion of a file from s3 storage."""
        try:
            s3_key = self._extract_s3_key(file_path)
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
        except ClientError as e:
            raise RuntimeError(f"Error deleting file from S3. Reason: {e}")
        
        # Always delete from local storage
        self.local_storage.delete_file(file_path)


    def delete_all_files(self) -> None:
        """Handles deletions of all files from s3 storage."""
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            if "Contents" in response:
                for content in response["Contents"]:
                    # Skip objects that were not uploaded from open-knowledge in the first place
                    if not content["Key"].startswith(self.key_prefix):
                        continue

                    self.s3_client.delete_object(
                        Bucket=self.bucket_name, 
                        Key=content["Key"]
                    )
        except ClientError as e:
            raise RuntimeError(f"Error deleting all files from S3. Reason: {e}")

        # Always delete files from local storage
        self.local_storage.delete_all_files()

    # The s3 key is the name assigned to an object. It excludes the bucket name, but includes the internal path and the filename.
    def _extract_s3_key(self, full_file_path: str) -> str:
        return "/".join(full_file_path.split("//")[1].split("/")[1:])


    def _get_local_file_path(self, s3_key: str) -> str:
        return f"{UPLOAD_DIR}/{s3_key.split('/')[-1]}"


def get_storage_provider(storage_provider: str):
    if storage_provider == "local":
        Storage = LoacalStorageProvider()
    elif storage_provider == "s3":
        Storage = S3StorageProvider()
    else:
        raise RuntimeError(f"Unsupported storage provider: {storage_provider}")

    return Storage


Storage = get_storage_provider(STORAGE_PROVIDER)