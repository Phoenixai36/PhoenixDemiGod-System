#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data Migration Utility for Phoenix DemiGod

This module provides tools to migrate data between different storage systems,
handle schema changes, and ensure data consistency during upgrades.
"""

import argparse
import json
import logging
import os
import shutil
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Union

import pymongo
import redis
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/data_migration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DataMigration")

# Load environment variables
load_dotenv()

class DataMigration:
    """
    Utility for migrating data between different storage systems and versions.
    """
    
    def __init__(self, source_config: Dict = None, target_config: Dict = None):
        """
        Initialize the data migration utility.
        
        Args:
            source_config: Configuration for the source database
            target_config: Configuration for the target database
        """
        # Default configurations
        self.source_config = source_config or {
            "type": os.getenv("SOURCE_DB_TYPE", "mongodb"),
            "uri": os.getenv("SOURCE_DB_URI", "mongodb://localhost:27017/phoenix"),
            "db_name": os.getenv("SOURCE_DB_NAME", "phoenix"),
        }
        
        self.target_config = target_config or {
            "type": os.getenv("TARGET_DB_TYPE", "mongodb"),
            "uri": os.getenv("TARGET_DB_URI", "mongodb://localhost:27017/phoenix_new"),
            "db_name": os.getenv("TARGET_DB_NAME", "phoenix_new"),
        }
        
        self.source_connection = None
        self.target_connection = None
        
        # Schema version mapping
        self.schema_versions = {
            "1.0": {
                "conversations": ["_id", "user_id", "messages", "created_at", "updated_at"],
                "knowledge": ["_id", "title", "content", "keywords", "created_at"]
            },
            "2.0": {
                "conversations": ["_id", "user_id", "messages", "metadata", "created_at", "updated_at"],
                "knowledge": ["_id", "title", "content", "keywords", "embeddings", "created_at", "domain"]
            }
        }
        
        self.current_version = os.getenv("DB_SCHEMA_VERSION", "1.0")
        self.target_version = os.getenv("TARGET_SCHEMA_VERSION", "2.0")
    
    def connect(self) -> bool:
        """
        Connect to source and target databases.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Connect to source database
            if self.source_config["type"] == "mongodb":
                self.source_client = pymongo.MongoClient(self.source_config["uri"])
                self.source_db = self.source_client[self.source_config["db_name"]]
                logger.info(f"Connected to source MongoDB: {self.source_config['db_name']}")
            
            elif self.source_config["type"] == "redis":
                self.source_client = redis.Redis.from_url(self.source_config["uri"])
                logger.info(f"Connected to source Redis: {self.source_config['uri']}")
            
            elif self.source_config["type"] == "file":
                if not os.path.exists(self.source_config["uri"]):
                    logger.error(f"Source file not found: {self.source_config['uri']}")
                    return False
                logger.info(f"Using source file: {self.source_config['uri']}")
            
            else:
                logger.error(f"Unsupported source database type: {self.source_config['type']}")
                return False
            
            # Connect to target database
            if self.target_config["type"] == "mongodb":
                self.target_client = pymongo.MongoClient(self.target_config["uri"])
                self.target_db = self.target_client[self.target_config["db_name"]]
                logger.info(f"Connected to target MongoDB: {self.target_config['db_name']}")
            
            elif self.target_config["type"] == "redis":
                self.target_client = redis.Redis.from_url(self.target_config["uri"])
                logger.info(f"Connected to target Redis: {self.target_config['uri']}")
            
            elif self.target_config["type"] == "file":
                target_dir = os.path.dirname(self.target_config["uri"])
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                logger.info(f"Using target file: {self.target_config['uri']}")
            
            else:
                logger.error(f"Unsupported target database type: {self.target_config['type']}")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return False
    
    def close_connections(self):
        """Close database connections."""
        if hasattr(self, 'source_client') and self.source_client and self.source_config["type"] in ["mongodb"]:
            self.source_client.close()
        
        if hasattr(self, 'target_client') and self.target_client and self.target_config["type"] in ["mongodb"]:
            self.target_client.close()
    
    def _transform_document(self, document: Dict, source_schema: List[str], target_schema: List[str]) -> Dict:
        """
        Transform a document from source schema to target schema.
        
        Args:
            document: The document to transform
            source_schema: Source schema field list
            target_schema: Target schema field list
            
        Returns:
            Transformed document
        """
        result = {}
        
        # Copy existing fields
        for field in source_schema:
            if field in document:
                result[field] = document[field]
        
        # Add new fields with default values
        for field in target_schema:
            if field not in source_schema and field not in result:
                if field == "metadata":
                    result[field] = {"migrated": True, "version": self.current_version}
                elif field == "embeddings":
                    result[field] = []
                elif field == "domain":
                    result[field] = "general"
                elif field.endswith("_at"):
                    result[field] = datetime.now()
        
        return result
    
    def migrate_collection(self, collection_name: str) -> Dict:
        """
        Migrate a single collection from source to target.
        
        Args:
            collection_name: Name of the collection to migrate
            
        Returns:
            Migration statistics
        """
        logger.info(f"Migrating collection: {collection_name}")
        
        start_time = time.time()
        stats = {"processed": 0, "success": 0, "failed": 0}
        
        try:
            # Get schema definitions
            source_schema = self.schema_versions[self.current_version].get(collection_name, [])
            target_schema = self.schema_versions[self.target_version].get(collection_name, [])
            
            if not source_schema or not target_schema:
                logger.error(f"Schema not found for collection: {collection_name}")
                return stats
            
            # MongoDB to MongoDB migration
            if self.source_config["type"] == "mongodb" and self.target_config["type"] == "mongodb":
                source_collection = self.source_db[collection_name]
                target_collection = self.target_db[collection_name]
                
                # Create index if needed
                if "user_id" in target_schema:
                    target_collection.create_index("user_id")
                if "keywords" in target_schema:
                    target_collection.create_index("keywords")
                
                # Process each document
                cursor = source_collection.find({})
                for doc in cursor:
                    stats["processed"] += 1
                    try:
                        transformed_doc = self._transform_document(doc, source_schema, target_schema)
                        target_collection.insert_one(transformed_doc)
                        stats["success"] += 1
                    except Exception as e:
                        logger.error(f"Failed to migrate document {doc.get('_id')}: {str(e)}")
                        stats["failed"] += 1
            
            # File to MongoDB migration
            elif self.source_config["type"] == "file" and self.target_config["type"] == "mongodb":
                target_collection = self.target_db[collection_name]
                
                with open(self.source_config["uri"], 'r') as f:
                    data = json.load(f)
                
                for item in data.get(collection_name, []):
                    stats["processed"] += 1
                    try:
                        transformed_doc = self._transform_document(item, source_schema, target_schema)
                        target_collection.insert_one(transformed_doc)
                        stats["success"] += 1
                    except Exception as e:
                        logger.error(f"Failed to migrate document: {str(e)}")
                        stats["failed"] += 1
            
            # MongoDB to file migration
            elif self.source_config["type"] == "mongodb" and self.target_config["type"] == "file":
                source_collection = self.source_db[collection_name]
                
                data = {collection_name: []}
                cursor = source_collection.find({})
                
                for doc in cursor:
                    stats["processed"] += 1
                    try:
                        # Convert ObjectId to string for JSON serialization
                        if "_id" in doc:
                            doc["_id"] = str(doc["_id"])
                        
                        transformed_doc = self._transform_document(doc, source_schema, target_schema)
                        data[collection_name].append(transformed_doc)
                        stats["success"] += 1
                    except Exception as e:
                        logger.error(f"Failed to migrate document: {str(e)}")
                        stats["failed"] += 1
                
                with open(self.target_config["uri"], 'w') as f:
                    json.dump(data, f)
            
            else:
                logger.error(f"Unsupported migration combination: {self.source_config['type']} to {self.target_config['type']}")
        
        except Exception as e:
            logger.error(f"Migration error for collection {collection_name}: {str(e)}")
        
        elapsed_time = time.time() - start_time
        stats["elapsed_time"] = elapsed_time
        
        logger.info(f"Migration of {collection_name} completed. Stats: {stats}")
        return stats
    
    def migrate_all(self) -> Dict:
        """
        Migrate all collections from source to target.
        
        Returns:
            Migration statistics
        """
        logger.info(f"Starting migration from version {self.current_version} to {self.target_version}")
        
        if not self.connect():
            return {"error": "Failed to connect to databases"}
        
        start_time = time.time()
        all_stats = {}
        
        try:
            # Get collections from the current schema version
            collections = self.schema_versions[self.current_version].keys()
            
            for collection_name in collections:
                all_stats[collection_name] = self.migrate_collection(collection_name)
            
            # Create backup of source data if needed
            if os.getenv("CREATE_BACKUP", "true").lower() == "true":
                self._create_backup()
        
        except Exception as e:
            logger.error(f"Migration error: {str(e)}")
            all_stats["error"] = str(e)
        
        finally:
            self.close_connections()
        
        elapsed_time = time.time() - start_time
        all_stats["total_elapsed_time"] = elapsed_time
        
        logger.info(f"Total migration completed. Elapsed time: {elapsed_time:.2f} seconds")
        return all_stats
    
    def _create_backup(self):
        """Create a backup of the source data."""
        backup_dir = os.getenv("BACKUP_DIR", "backups")
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/backup_{self.current_version}_{timestamp}.json"
        
        logger.info(f"Creating backup at {backup_file}")
        
        backup_data = {}
        
        # MongoDB backup
        if self.source_config["type"] == "mongodb":
            for collection_name in self.schema_versions[self.current_version].keys():
                backup_data[collection_name] = []
                source_collection = self.source_db[collection_name]
                cursor = source_collection.find({})
                
                for doc in cursor:
                    # Convert ObjectId to string for JSON serialization
                    if "_id" in doc:
                        doc["_id"] = str(doc["_id"])
                    
                    backup_data[collection_name].append(doc)
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f)
        
        # File backup
        elif self.source_config["type"] == "file":
            shutil.copy2(self.source_config["uri"], backup_file)
        
        logger.info(f"Backup created successfully at {backup_file}")

def main():
    """Command line interface for the data migration utility."""
    parser = argparse.ArgumentParser(description="Phoenix DemiGod Data Migration Utility")
    parser.add_argument("--source-type", choices=["mongodb", "redis", "file"], help="Source database type")
    parser.add_argument("--source-uri", help="Source database URI or file path")
    parser.add_argument("--source-db", help="Source database name")
    parser.add_argument("--target-type", choices=["mongodb", "redis", "file"], help="Target database type")
    parser.add_argument("--target-uri", help="Target database URI or file path")
    parser.add_argument("--target-db", help="Target database name")
    parser.add_argument("--current-version", help="Current schema version")
    parser.add_argument("--target-version", help="Target schema version")
    parser.add_argument("--collection", help="Specific collection to migrate (default: all)")
    parser.add_argument("--backup", action="store_true", help="Create backup of source data")
    args = parser.parse_args()
    
    # Override environment variables with command line arguments
    source_config = {}
    target_config = {}
    
    if args.source_type:
        source_config["type"] = args.source_type
    if args.source_uri:
        source_config["uri"] = args.source_uri
    if args.source_db:
        source_config["db_name"] = args.source_db
    
    if args.target_type:
        target_config["type"] = args.target_type
    if args.target_uri:
        target_config["uri"] = args.target_uri
    if args.target_db:
        target_config["db_name"] = args.target_db
    
    if args.backup:
        os.environ["CREATE_BACKUP"] = "true"
    
    if args.current_version:
        os.environ["DB_SCHEMA_VERSION"] = args.current_version
    
    if args.target_version:
        os.environ["TARGET_SCHEMA_VERSION"] = args.target_version
    
    # Create migration instance
    migration = DataMigration(source_config or None, target_config or None)
    
    # Perform migration
    if args.collection:
        if not migration.connect():
            logger.error("Failed to connect to databases")
            return 1
        
        stats = migration.migrate_collection(args.collection)
        migration.close_connections()
        
        print(json.dumps(stats, indent=2))
    else:
        stats = migration.migrate_all()
        print(json.dumps(stats, indent=2))
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
