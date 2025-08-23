from google.cloud import bigquery
from google.cloud.bigquery import SchemaField
from config import Config
import logging
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BigQueryService:
    def __init__(self):
        try:
            self.client = bigquery.Client(project=Config.GCP_PROJECT)
            self.dataset_id = Config.BQ_DATASET
            self._ensure_dataset_exists()
            self._ensure_tables_exist()
            logger.info("BigQuery client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            raise
    
    def _ensure_dataset_exists(self):
        """Ensure the analytics dataset exists"""
        try:
            dataset_ref = self.client.dataset(self.dataset_id)
            try:
                self.client.get_dataset(dataset_ref)
                logger.info(f"Dataset {self.dataset_id} already exists")
            except Exception:
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = Config.GCP_LOCATION
                dataset = self.client.create_dataset(dataset)
                logger.info(f"Created dataset {self.dataset_id}")
        except Exception as e:
            logger.error(f"Failed to ensure dataset exists: {e}")
    
    def _ensure_tables_exist(self):
        """Ensure required tables exist"""
        try:
            # Mood logs table schema
            mood_schema = [
                SchemaField("user_id", "STRING", mode="REQUIRED"),
                SchemaField("mood", "STRING", mode="REQUIRED"),
                SchemaField("energy", "INTEGER", mode="NULLABLE"),
                SchemaField("stress", "INTEGER", mode="NULLABLE"),
                SchemaField("note", "STRING", mode="NULLABLE"),
                SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                SchemaField("created_at", "TIMESTAMP", mode="REQUIRED")
            ]
            
            # Journal insights table schema
            journal_schema = [
                SchemaField("user_id", "STRING", mode="REQUIRED"),
                SchemaField("categories", "STRING", mode="REPEATED"),
                SchemaField("mood", "STRING", mode="NULLABLE"),
                SchemaField("risk_level", "STRING", mode="NULLABLE"),
                SchemaField("confidence", "FLOAT", mode="NULLABLE"),
                SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                SchemaField("created_at", "TIMESTAMP", mode="REQUIRED")
            ]
            
            self._create_table_if_not_exists(Config.BQ_MOOD_TABLE, mood_schema)
            self._create_table_if_not_exists(Config.BQ_JOURNAL_TABLE, journal_schema)
            
        except Exception as e:
            logger.error(f"Failed to ensure tables exist: {e}")
    
    def _create_table_if_not_exists(self, table_name: str, schema: list):
        """Create table if it doesn't exist"""
        try:
            table_ref = self.client.dataset(self.dataset_id).table(table_name)
            try:
                self.client.get_table(table_ref)
                logger.info(f"Table {table_name} already exists")
            except Exception:
                table = bigquery.Table(table_ref, schema=schema)
                table = self.client.create_table(table)
                logger.info(f"Created table {table_name}")
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
    
    def stream_mood_log(self, mood_data: Dict[str, Any]) -> bool:
        """Stream mood log data to BigQuery"""
        try:
            table_ref = self.client.dataset(self.dataset_id).table(Config.BQ_MOOD_TABLE)
            
            # Prepare row data
            row_data = {
                "user_id": mood_data.get("user_id"),
                "mood": mood_data.get("mood"),
                "energy": mood_data.get("energy"),
                "stress": mood_data.get("stress"),
                "note": mood_data.get("note"),
                "timestamp": mood_data.get("timestamp", datetime.now(timezone.utc)).isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Insert row
            errors = self.client.insert_rows_json(table_ref, [row_data])
            
            if errors:
                logger.error(f"Failed to insert mood log: {errors}")
                return False
            
            logger.info("Mood log streamed to BigQuery successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stream mood log to BigQuery: {e}")
            return False
    
    def stream_journal_insight(self, journal_data: Dict[str, Any]) -> bool:
        """Stream journal insight data to BigQuery"""
        try:
            table_ref = self.client.dataset(self.dataset_id).table(Config.BQ_JOURNAL_TABLE)
            
            # Prepare row data
            ai_insight = journal_data.get("ai_insight", {})
            row_data = {
                "user_id": journal_data.get("user_id"),
                "categories": ai_insight.get("categories", []),
                "mood": ai_insight.get("mood"),
                "risk_level": ai_insight.get("risk"),
                "confidence": ai_insight.get("confidence"),
                "timestamp": journal_data.get("timestamp", datetime.now(timezone.utc)).isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Insert row
            errors = self.client.insert_rows_json(table_ref, [row_data])
            
            if errors:
                logger.error(f"Failed to insert journal insight: {errors}")
                return False
            
            logger.info("Journal insight streamed to BigQuery successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stream journal insight to BigQuery: {e}")
            return False

bigquery_service = BigQueryService()
