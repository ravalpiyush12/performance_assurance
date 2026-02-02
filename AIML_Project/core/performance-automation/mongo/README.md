Common Connection Examples:
If you use Compass with localhost:
json{
  "mongodb": {
    "host": "localhost",
    "port": 27017,
    "database": "your_db_name",
    "username": "",
    "password": ""
  }
}
If you use Compass with authentication:
json{
  "mongodb": {
    "host": "your-server.com",
    "port": 27017,
    "database": "your_db_name",
    "username": "your_username",
    "password": "your_password",
    "auth_source": "admin"
  }
}
If you use Compass with MongoDB Atlas:
json{
  "mongodb": {
    "host": "cluster0.xxxxx.mongodb.net",
    "port": 27017,
    "database": "your_db_name",
    "username": "your_username",
    "password": "your_password",
    "auth_source": "admin"
  }
}
What Happens When You Run It:

Connects to MongoDB (same connection as Compass uses)
Reads all documents from specified collections
Flattens nested fields (e.g., user.address.city becomes user_address_city)
Creates Excel files with:

Formatted headers (blue background, white text)
Auto-filter enabled
Frozen top row
Auto-adjusted column widths


Saves to exports/ folder with timestamps

Quick Troubleshooting:
If test_mongo_connection.py works but export fails:

Check the collection names in config file
Ensure you have write permissions to exports/ folder

If you get "No module named 'pymongo'":
bashpip install --break-system-packages pymongo openpyxl
To see exactly what Compass uses:

In Compass, go to: ⋮ (three dots) → Copy Connection String
Use those values in the config

Would you like me to add any specific features like:

Email notification when export completes
Export only documents modified in last X days
Split large collections into multiple Excel sheets
Custom field selection/renaming