"""
MongoDB Collections Analysis Handler
Handles MongoDB collection analysis and monitoring
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import json
from config import Settings

logger = logging.getLogger(__name__)


class MongoDBConfig:
    """MongoDB configuration"""
    
    def __init__(self, settings: Settings):
        self.connection_string = settings.MONGODB_CONNECTION_STRING
        self.database_name = settings.MONGODB_DATABASE
        self.timeout = settings.MONGODB_TIMEOUT
        self.max_pool_size = settings.MONGODB_MAX_POOL_SIZE


class MongoDBAnalyzer:
    """MongoDB collections analysis operations"""
    
    def __init__(self, config: MongoDBConfig):
        self.config = config
        self.client: Optional[MongoClient] = None
        self.db = None
        self.monitoring_active = False
        self.last_analysis_time = None
        self.analysis_config = {}
        
    def connect(self):
        """Establish MongoDB connection"""
        try:
            if not self.client:
                logger.info("Connecting to MongoDB...")
                
                self.client = MongoClient(
                    self.config.connection_string,
                    serverSelectionTimeoutMS=self.config.timeout * 1000,
                    maxPoolSize=self.config.max_pool_size
                )
                
                # Test connection
                self.client.admin.command('ping')
                
                self.db = self.client[self.config.database_name]
                
                logger.info("MongoDB connection established successfully")
                
        except ConnectionFailure as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise Exception(f"Failed to connect to MongoDB: {e}")
    
    def start_analysis(
        self,
        database_name: Optional[str] = None,
        collections: Optional[List[str]] = None,
        analysis_interval_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Start MongoDB collections analysis
        
        Args:
            database_name: Database to analyze
            collections: Specific collections (None = all)
            analysis_interval_minutes: Analysis duration
            
        Returns:
            Status and configuration
        """
        try:
            self.connect()
            
            db_name = database_name or self.config.database_name
            
            logger.info(f"Starting MongoDB analysis for database: {db_name}")
            
            # Switch database if different
            if db_name != self.config.database_name:
                self.db = self.client[db_name]
            
            # Get all collections or use specified
            if collections:
                target_collections = collections
            else:
                target_collections = self.db.list_collection_names()
            
            # Get initial statistics
            initial_stats = self._get_database_stats()
            
            # Store analysis configuration
            self.analysis_config = {
                "database": db_name,
                "collections": target_collections,
                "interval_minutes": analysis_interval_minutes,
                "start_time": datetime.now()
            }
            
            self.monitoring_active = True
            self.last_analysis_time = datetime.now()
            
            result = {
                "status": "started",
                "database": db_name,
                "collections_count": len(target_collections),
                "collections": target_collections[:10],  # First 10
                "analysis_interval_minutes": analysis_interval_minutes,
                "start_time": self.last_analysis_time.isoformat(),
                "end_time": (self.last_analysis_time + timedelta(minutes=analysis_interval_minutes)).isoformat(),
                "initial_stats": initial_stats,
                "monitoring_active": self.monitoring_active
            }
            
            logger.info(f"MongoDB analysis started for {len(target_collections)} collections")
            return result
            
        except Exception as e:
            logger.error(f"Failed to start MongoDB analysis: {e}")
            raise Exception(f"MongoDB analysis start failed: {e}")
    
    def stop_analysis(self) -> Dict[str, Any]:
        """
        Stop MongoDB collections analysis
        
        Returns:
            Final status and summary
        """
        try:
            logger.info("Stopping MongoDB analysis")
            
            if not self.monitoring_active:
                return {
                    "status": "not_active",
                    "message": "Analysis was not active"
                }
            
            # Get final statistics
            final_stats = None
            if self.analysis_config:
                final_stats = self._get_database_stats()
            
            duration = None
            if self.analysis_config.get("start_time"):
                duration = (datetime.now() - self.analysis_config["start_time"]).total_seconds() / 60
            
            self.monitoring_active = False
            
            result = {
                "status": "stopped",
                "stop_time": datetime.now().isoformat(),
                "duration_minutes": round(duration, 2) if duration else None,
                "final_stats": final_stats,
                "monitoring_active": self.monitoring_active
            }
            
            logger.info("MongoDB analysis stopped successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to stop MongoDB analysis: {e}")
            raise Exception(f"MongoDB analysis stop failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current analysis status"""
        return {
            "monitoring_active": self.monitoring_active,
            "last_analysis_time": self.last_analysis_time.isoformat() if self.last_analysis_time else None,
            "database": self.analysis_config.get("database") if self.analysis_config else self.config.database_name,
            "connected": self.client is not None,
            "config": self.analysis_config if self.monitoring_active else None
        }
    
    def analyze_collection(
        self,
        collection_name: str,
        sample_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Analyze a specific collection
        
        Args:
            collection_name: Collection to analyze
            sample_size: Sample size for analysis
            
        Returns:
            Collection analysis
        """
        try:
            self.connect()
            
            logger.info(f"Analyzing collection: {collection_name}")
            
            collection = self.db[collection_name]
            
            # Get collection stats
            stats = self.db.command("collStats", collection_name)
            
            # Document count
            doc_count = collection.count_documents({})
            
            # Sample documents for schema analysis
            sample_docs = list(collection.find().limit(sample_size))
            
            # Analyze schema
            schema_analysis = self._analyze_schema(sample_docs)
            
            # Get indexes
            indexes = list(collection.list_indexes())
            
            # Size information
            size_info = {
                "count": stats.get("count", 0),
                "size_bytes": stats.get("size", 0),
                "size_mb": round(stats.get("size", 0) / (1024 * 1024), 2),
                "avg_obj_size": stats.get("avgObjSize", 0),
                "storage_size_bytes": stats.get("storageSize", 0),
                "storage_size_mb": round(stats.get("storageSize", 0) / (1024 * 1024), 2),
                "total_index_size_bytes": stats.get("totalIndexSize", 0),
                "total_index_size_mb": round(stats.get("totalIndexSize", 0) / (1024 * 1024), 2)
            }
            
            return {
                "status": "success",
                "collection": collection_name,
                "document_count": doc_count,
                "size_info": size_info,
                "indexes_count": len(indexes),
                "indexes": [{"name": idx["name"], "key": idx["key"]} for idx in indexes],
                "schema_analysis": schema_analysis,
                "sample_size": len(sample_docs),
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze collection {collection_name}: {e}")
            raise Exception(f"Collection analysis failed: {e}")
    
    def analyze_all_collections(
        self,
        database_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze all collections in database
        
        Args:
            database_name: Database name
            
        Returns:
            Analysis of all collections
        """
        try:
            self.connect()
            
            db_name = database_name or self.config.database_name
            db = self.client[db_name]
            
            logger.info(f"Analyzing all collections in database: {db_name}")
            
            collections = db.list_collection_names()
            
            analyses = []
            total_documents = 0
            total_size_mb = 0
            
            for coll_name in collections:
                try:
                    analysis = self.analyze_collection(coll_name)
                    analyses.append(analysis)
                    total_documents += analysis["document_count"]
                    total_size_mb += analysis["size_info"]["size_mb"]
                except Exception as e:
                    logger.warning(f"Failed to analyze collection {coll_name}: {e}")
                    analyses.append({
                        "collection": coll_name,
                        "status": "error",
                        "error": str(e)
                    })
            
            return {
                "status": "success",
                "database": db_name,
                "collections_count": len(collections),
                "total_documents": total_documents,
                "total_size_mb": round(total_size_mb, 2),
                "collections_analysis": analyses,
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze all collections: {e}")
            raise Exception(f"All collections analysis failed: {e}")
    
    def get_slow_queries(
        self,
        database_name: Optional[str] = None,
        threshold_ms: int = 100,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get slow queries from system.profile
        
        Args:
            database_name: Database name
            threshold_ms: Slow query threshold in milliseconds
            limit: Maximum results
            
        Returns:
            Slow queries
        """
        try:
            self.connect()
            
            db_name = database_name or self.config.database_name
            db = self.client[db_name]
            
            logger.info(f"Fetching slow queries for database: {db_name}")
            
            # Check if profiling is enabled
            profile_level = db.command("profile", -1)
            
            if profile_level.get("was", 0) == 0:
                return {
                    "status": "warning",
                    "message": "Database profiling is not enabled",
                    "profile_level": 0
                }
            
            # Query system.profile
            slow_queries = list(
                db.system.profile.find(
                    {"millis": {"$gte": threshold_ms}}
                ).sort("millis", -1).limit(limit)
            )
            
            # Format results
            formatted_queries = []
            for query in slow_queries:
                formatted_queries.append({
                    "timestamp": query.get("ts", ""),
                    "duration_ms": query.get("millis", 0),
                    "operation": query.get("op", ""),
                    "namespace": query.get("ns", ""),
                    "command": str(query.get("command", {}))[:200]  # Truncate
                })
            
            return {
                "status": "success",
                "database": db_name,
                "threshold_ms": threshold_ms,
                "slow_queries_count": len(formatted_queries),
                "slow_queries": formatted_queries,
                "profile_level": profile_level.get("was", 0),
                "fetched_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            raise Exception(f"Slow queries fetch failed: {e}")
    
    def get_database_statistics(
        self,
        database_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive database statistics
        
        Args:
            database_name: Database name
            
        Returns:
            Database statistics
        """
        try:
            self.connect()
            
            db_name = database_name or self.config.database_name
            db = self.client[db_name]
            
            logger.info(f"Fetching database statistics for: {db_name}")
            
            stats = db.command("dbStats")
            
            return {
                "status": "success",
                "database": db_name,
                "collections": stats.get("collections", 0),
                "views": stats.get("views", 0),
                "objects": stats.get("objects", 0),
                "avg_obj_size": stats.get("avgObjSize", 0),
                "data_size_bytes": stats.get("dataSize", 0),
                "data_size_mb": round(stats.get("dataSize", 0) / (1024 * 1024), 2),
                "storage_size_bytes": stats.get("storageSize", 0),
                "storage_size_mb": round(stats.get("storageSize", 0) / (1024 * 1024), 2),
                "indexes": stats.get("indexes", 0),
                "index_size_bytes": stats.get("indexSize", 0),
                "index_size_mb": round(stats.get("indexSize", 0) / (1024 * 1024), 2),
                "total_size_bytes": stats.get("dataSize", 0) + stats.get("indexSize", 0),
                "total_size_mb": round((stats.get("dataSize", 0) + stats.get("indexSize", 0)) / (1024 * 1024), 2),
                "fetched_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
            raise Exception(f"Database statistics fetch failed: {e}")
    
    def _get_database_stats(self) -> Dict[str, Any]:
        """Get quick database stats"""
        try:
            if not self.db:
                return {}
            
            stats = self.db.command("dbStats")
            
            return {
                "collections": stats.get("collections", 0),
                "objects": stats.get("objects", 0),
                "data_size_mb": round(stats.get("dataSize", 0) / (1024 * 1024), 2),
                "index_size_mb": round(stats.get("indexSize", 0) / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.warning(f"Failed to get database stats: {e}")
            return {}
    
    def _analyze_schema(self, documents: List[Dict]) -> Dict[str, Any]:
        """Analyze schema from sample documents"""
        if not documents:
            return {"fields": {}, "field_count": 0}
        
        field_types = {}
        field_null_counts = {}
        
        for doc in documents:
            for field, value in doc.items():
                if field not in field_types:
                    field_types[field] = set()
                    field_null_counts[field] = 0
                
                if value is None:
                    field_null_counts[field] += 1
                else:
                    field_types[field].add(type(value).__name__)
        
        # Format results
        fields = {}
        for field, types in field_types.items():
            fields[field] = {
                "types": list(types),
                "null_count": field_null_counts[field],
                "null_percentage": round((field_null_counts[field] / len(documents)) * 100, 2)
            }
        
        return {
            "field_count": len(fields),
            "fields": fields,
            "sample_size": len(documents)
        }
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            try:
                self.client.close()
                logger.info("MongoDB connection closed")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {e}")
            finally:
                self.client = None
                self.db = None