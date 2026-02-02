# test_mongo_connection.py
import pymongo
from pymongo import MongoClient
import json

def test_connection():
    """
    Test script to verify MongoDB connection and list collections
    Similar to what you see in MongoDB Compass
    """
    
    # STEP 1: Get your connection details from Compass
    # In Compass, click on the connection - you'll see something like:
    # mongodb://username:password@host:port/database
    # OR just: mongodb://localhost:27017
    
    print("=" * 60)
    print("MongoDB Connection Test")
    print("=" * 60)
    
    # Enter your connection details here (same as in Compass)
    HOST = input("Enter MongoDB host (default: localhost): ").strip() or "localhost"
    PORT = input("Enter MongoDB port (default: 27017): ").strip() or "27017"
    DATABASE = input("Enter database name: ").strip()
    USERNAME = input("Enter username (press Enter if none): ").strip()
    PASSWORD = input("Enter password (press Enter if none): ").strip()
    
    try:
        # Build connection string
        if USERNAME and PASSWORD:
            connection_string = f"mongodb://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/"
        else:
            connection_string = f"mongodb://{HOST}:{PORT}/"
        
        print(f"\nConnecting to: {connection_string.replace(PASSWORD, '****') if PASSWORD else connection_string}")
        
        # Connect
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.server_info()
        print("✓ Connection successful!")
        
        # Access database
        db = client[DATABASE]
        
        # List all collections (like you see in Compass)
        collections = db.list_collection_names()
        print(f"\n✓ Found {len(collections)} collections in database '{DATABASE}':")
        print("-" * 60)
        
        for i, coll_name in enumerate(collections, 1):
            # Get document count
            count = db[coll_name].count_documents({})
            print(f"{i}. {coll_name} ({count} documents)")
        
        # Ask user which collection to preview
        print("\n" + "=" * 60)
        choice = input("\nEnter collection name to preview (or press Enter to skip): ").strip()
        
        if choice and choice in collections:
            print(f"\nFetching first 3 documents from '{choice}'...")
            print("-" * 60)
            
            collection = db[choice]
            documents = list(collection.find().limit(3))
            
            for i, doc in enumerate(documents, 1):
                print(f"\nDocument {i}:")
                print(json.dumps(doc, indent=2, default=str))
            
            print(f"\n✓ Successfully retrieved data from '{choice}'")
            print(f"✓ This collection has {len(documents[0].keys()) if documents else 0} fields")
        
        # Save configuration for later use
        save_config = input("\nSave these settings to config file? (y/n): ").strip().lower()
        
        if save_config == 'y':
            config = {
                "mongodb": {
                    "host": HOST,
                    "port": int(PORT),
                    "database": DATABASE,
                    "username": USERNAME,
                    "password": PASSWORD,
                    "auth_source": "admin"
                },
                "collections": collections,
                "output": {
                    "directory": "exports",
                    "filename_prefix": "mongodb_export",
                    "add_timestamp": True
                },
                "excel": {
                    "header_style": {
                        "bold": True,
                        "bg_color": "366092",
                        "font_color": "FFFFFF"
                    },
                    "auto_filter": True,
                    "freeze_panes": True
                }
            }
            
            with open('mongo_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            print("\n✓ Configuration saved to 'mongo_config.json'")
            print("✓ You can now run the main export script")
        
        client.close()
        
        print("\n" + "=" * 60)
        print("Test completed successfully!")
        print("=" * 60)
        
        return True
        
    except pymongo.errors.ServerSelectionTimeoutError:
        print("\n✗ Error: Could not connect to MongoDB server")
        print("  Check if:")
        print("  - MongoDB is running")
        print("  - Host and port are correct")
        print("  - Network/firewall allows connection")
        return False
        
    except pymongo.errors.OperationFailure as e:
        print(f"\n✗ Authentication failed: {str(e)}")
        print("  Check your username and password")
        return False
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return False


if __name__ == '__main__':
    test_connection()