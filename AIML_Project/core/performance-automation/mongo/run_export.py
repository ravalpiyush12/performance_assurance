# run_export.py
from mongo_to_excel import MongoToExcelExporter
import logging

logging.basicConfig(level=logging.INFO)

def main():
    print("Starting MongoDB to Excel Export...")
    print("-" * 60)
    
    # Initialize exporter (reads from mongo_config.json)
    exporter = MongoToExcelExporter('mongo_config.json')
    
    # Connect
    if not exporter.connect():
        print("Failed to connect. Please run test_mongo_connection.py first")
        return
    
    # Option 1: Export ALL collections
    print("\nExporting all collections...")
    created_files = exporter.export_collections()
    
    # Option 2: Export specific collections (uncomment to use)
    # created_files = exporter.export_collections(['collection1', 'collection2'])
    
    # Option 3: Export with query filter (uncomment to use)
    # data = exporter.get_collection_data(
    #     'your_collection_name',
    #     query={'status': 'active'},  # Your filter
    #     limit=1000  # Optional limit
    # )
    # exporter.create_excel(data, 'filtered_export.xlsx')
    
    # Show results
    print("\n" + "=" * 60)
    print(f"Export completed! Created {len(created_files)} files:")
    for file_path in created_files:
        print(f"  ✓ {file_path}")
    print("=" * 60)
    
    # Cleanup
    exporter.close()


if __name__ == '__main__':
    main()