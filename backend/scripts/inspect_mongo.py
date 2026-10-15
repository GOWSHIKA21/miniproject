"""
Quick Interactive MongoDB Inspector for PatentGraph AI.
Run this script to browse and view documents directly inside MongoDB.
"""
import sys
from pymongo import MongoClient
import json

def inspect():
    client = MongoClient("mongodb://localhost:27017")
    db = client["patentgraph_db"]
    col = db["patents_2016_2018"]
    
    total = col.count_documents({})
    print("=" * 60)
    print(f" MongoDB Database   : patentgraph_db")
    print(f" Collection Name    : patents_2016_2018")
    print(f" Total Documents    : {total}")
    print("=" * 60)
    
    # Show first 3 sample documents
    print("\n--- SAMPLE DOCUMENTS (First 3) ---\n")
    cursor = col.find({}, {"_id": 0}).limit(3)
    for i, doc in enumerate(cursor, 1):
        print(f"[{i}] Patent ID: {doc.get('patent_id')}")
        print(f"    Title      : {doc.get('title')}")
        print(f"    Field      : {doc.get('field_of_invention')}")
        print(f"    Date       : {doc.get('publication_date')}")
        print(f"    Office     : {doc.get('ipo_location')}")
        print(f"    Applicant  : {doc.get('applicant')}")
        abstract = doc.get('abstract', '')
        snippet = (abstract[:120] + '...') if len(abstract) > 120 else abstract
        print(f"    Abstract   : {snippet}\n")
        
    print("=" * 60)
    print("Tip: Run `python backend/scripts/inspect_mongo.py <patent_id>` to inspect any specific patent!")
    print("=" * 60)

def view_single(patent_id):
    client = MongoClient("mongodb://localhost:27017")
    col = client["patentgraph_db"]["patents_2016_2018"]
    doc = col.find_one({"patent_id": patent_id}, {"_id": 0})
    if not doc:
        # Case insensitive partial match
        doc = col.find_one({"patent_id": {"$regex": patent_id, "$options": "i"}}, {"_id": 0})
    
    if doc:
        print(f"\nDocument details for {doc.get('patent_id')}:\n")
        print(json.dumps(doc, indent=2, default=str))
    else:
        print(f"\nNo document found matching '{patent_id}' in patents_2016_2018.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        view_single(sys.argv[1])
    else:
        inspect()
