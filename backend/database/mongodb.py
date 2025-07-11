from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List, Dict, Any
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database = None

db = MongoDB()

async def connect_to_mongo():
    """Create database connection"""
    try:
        db.client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db.database = db.client[os.environ["DB_NAME"]]
        
        # Test connection
        await db.database.command('ping')
        logger.info("Connected to MongoDB successfully")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")

async def create_indexes():
    """Create database indexes for better performance"""
    try:
        # User indexes
        await db.database.users.create_index("email", unique=True)
        await db.database.users.create_index("role")
        
        # Project indexes
        await db.database.projects.create_index("created_by")
        await db.database.projects.create_index("status")
        await db.database.projects.create_index("team_members")
        
        # Task indexes
        await db.database.tasks.create_index("project_id")
        await db.database.tasks.create_index("assignee_id")
        await db.database.tasks.create_index("status")
        
        # Time entry indexes
        await db.database.time_entries.create_index("user_id")
        await db.database.time_entries.create_index("project_id")
        await db.database.time_entries.create_index("start_time")
        await db.database.time_entries.create_index([("user_id", 1), ("start_time", -1)])
        
        # Activity data indexes
        await db.database.activity_data.create_index("user_id")
        await db.database.activity_data.create_index("time_entry_id")
        await db.database.activity_data.create_index("timestamp")
        
        # Screenshot indexes
        await db.database.screenshots.create_index("user_id")
        await db.database.screenshots.create_index("time_entry_id")
        await db.database.screenshots.create_index("timestamp")
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")

# Database operations
class DatabaseOperations:
    
    @staticmethod
    async def create_document(collection: str, document: Dict[str, Any]) -> str:
        """Create a new document in the specified collection"""
        result = await db.database[collection].insert_one(document)
        return str(result.inserted_id)
    
    @staticmethod
    async def get_document(collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get a single document from the collection"""
        result = await db.database[collection].find_one(query)
        if result:
            result["_id"] = str(result["_id"])
        return result
    
    @staticmethod
    async def get_documents(collection: str, query: Dict[str, Any] = None, 
                          sort: List = None, limit: int = None, skip: int = 0) -> List[Dict[str, Any]]:
        """Get multiple documents from the collection"""
        if query is None:
            query = {}
        
        cursor = db.database[collection].find(query)
        
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        
        results = await cursor.to_list(length=limit)
        for result in results:
            result["_id"] = str(result["_id"])
        
        return results
    
    @staticmethod
    async def update_document(collection: str, query: Dict[str, Any], 
                            update: Dict[str, Any]) -> bool:
        """Update a document in the collection"""
        update["updated_at"] = datetime.utcnow()
        result = await db.database[collection].update_one(query, {"$set": update})
        return result.modified_count > 0
    
    @staticmethod
    async def delete_document(collection: str, query: Dict[str, Any]) -> bool:
        """Delete a document from the collection"""
        result = await db.database[collection].delete_one(query)
        return result.deleted_count > 0
    
    @staticmethod
    async def count_documents(collection: str, query: Dict[str, Any] = None) -> int:
        """Count documents in the collection"""
        if query is None:
            query = {}
        return await db.database[collection].count_documents(query)
    
    @staticmethod
    async def aggregate(collection: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform aggregation on the collection"""
        cursor = db.database[collection].aggregate(pipeline)
        results = await cursor.to_list(None)
        for result in results:
            if "_id" in result:
                result["_id"] = str(result["_id"])
        return results

# Get database instance
def get_database():
    return db.database