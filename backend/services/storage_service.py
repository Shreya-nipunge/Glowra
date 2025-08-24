from google.cloud import storage
from config import Config
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        try:
            self.client = storage.Client(project=Config.GCP_PROJECT)
            self.bucket_name = Config.GCS_BUCKET
            self.bucket = self.client.bucket(self.bucket_name)
            logger.info("Cloud Storage client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Cloud Storage client: {e}")
            raise
    
    def get_signed_url(self, blob_name: str, expiration_minutes: int = 60) -> Optional[str]:
        """Generate a signed URL for accessing a file in Cloud Storage"""
        try:
            blob = self.bucket.blob(blob_name)
            
            # Generate signed URL valid for specified minutes
            expiration = datetime.utcnow() + timedelta(minutes=expiration_minutes)
            
            url = blob.generate_signed_url(
                version="v4",
                expiration=expiration,
                method="GET"
            )
            
            logger.info(f"Generated signed URL for {blob_name}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate signed URL for {blob_name}: {e}")
            return None
    
    def list_meditation_files(self) -> list:
        """List available meditation audio files"""
        try:
            blobs = self.bucket.list_blobs(prefix="meditations/")
            
            meditation_files = []
            for blob in blobs:
                if blob.name.endswith(('.mp3', '.wav', '.m4a')):
                    file_info = {
                        'name': blob.name.split('/')[-1],
                        'path': blob.name,
                        'size': blob.size,
                        'created': blob.time_created.isoformat() if blob.time_created else None,
                        'url': self.get_signed_url(blob.name)
                    }
                    meditation_files.append(file_info)
            
            logger.info(f"Found {len(meditation_files)} meditation files")
            return meditation_files
            
        except Exception as e:
            logger.error(f"Failed to list meditation files: {e}")
            return []
    
    def upload_file(self, file_data: bytes, destination_path: str, content_type: str = None) -> bool:
        """Upload a file to Cloud Storage"""
        try:
            blob = self.bucket.blob(destination_path)
            
            if content_type:
                blob.content_type = content_type
            
            blob.upload_from_string(file_data)
            
            logger.info(f"File uploaded to {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload file to {destination_path}: {e}")
            return False

storage_service = StorageService()
