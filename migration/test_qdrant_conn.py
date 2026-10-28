#!/usr/bin/env python3
"""
PatentGraph AI - Qdrant Cloud Connectivity Diagnostic Tool
==========================================================
Diagnoses Qdrant Cloud connectivity, API key formatting, endpoint URL normalization,
and collection status without modifying data or uploading vectors.
"""

import os
import sys
import re
import socket
import logging
from pathlib import Path
from urllib.parse import urlparse

# Deterministic .env loading from backend/.env
PROJECT_ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    env_candidates = [
        Path.cwd() / "backend" / ".env",
        Path.cwd() / "miniproject" / "backend" / ".env",
        PROJECT_ROOT / "backend" / ".env",
        Path.cwd() / ".env",
        PROJECT_ROOT / ".env",
    ]
    loaded_env = None
    for candidate in env_candidates:
        if candidate.is_file():
            load_dotenv(dotenv_path=candidate, override=True)
            loaded_env = candidate
            break
except ImportError:
    pass

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TestQdrantConn")


def mask_url(url: str) -> str:
    if not url:
        return "[EMPTY]"
    return re.sub(r"://([^@]+)@", "://****@", url)


def normalize_qdrant_url(url: str) -> str:
    if not url:
        return ""
    cleaned = url.strip()
    if "cloud.qdrant.io:6333" in cleaned:
        cleaned = cleaned.replace(":6333", "")
    return cleaned


def test_qdrant():
    raw_url = os.getenv("QDRANT_URL", "")
    url = normalize_qdrant_url(raw_url)
    api_key = os.getenv("QDRANT_API_KEY", "")
    collection_name = os.getenv("QDRANT_COLLECTION", "patent_embeddings")

    print("\n" + "=" * 70)
    print("QDRANT CLOUD CONNECTIVITY DIAGNOSTIC")
    print("=" * 70)
    print(f"Target URL       : {mask_url(url)}")
    print(f"Target Collection: {collection_name}")
    print(f"API Key Status   : {'[SET - ' + str(len(api_key)) + ' chars]' if api_key else '[NOT SET]'}")
    print("-" * 70)

    if not url:
        print("[-] FAILED: QDRANT_URL is not configured in backend/.env.")
        return False

    # Check if user accidentally pasted URL into API Key
    if api_key and (api_key.startswith("http://") or api_key.startswith("https://") or api_key == url or api_key == raw_url):
        print("\n" + "!" * 70)
        print("CRITICAL DIAGNOSIS: QDRANT_API_KEY IS SET TO A URL!")
        print(f"Current QDRANT_API_KEY value in .env: '{api_key}'")
        print("\nWHY THIS FAILS (HTTP 403 Forbidden):")
        print("When connecting, Qdrant Cloud receives this URL as an authentication header token.")
        print("Because a URL is not a valid API key token, Qdrant Cloud returns HTTP 403 Forbidden.")
        print("\nHOW TO FIX:")
        print("  1. Log into your Qdrant Cloud Console: https://cloud.qdrant.io")
        print("  2. Select your Cluster (f926cdb3-3b12-47ea-9d60-e29fb6b159ff)")
        print("  3. Navigate to the 'API Keys' tab (or 'Data Access Control')")
        print("  4. Generate or copy your secret API Key token (e.g. an alphanumeric string)")
        print("  5. Open backend/.env and update QDRANT_API_KEY with your key token.")
        print("!" * 70 + "\n")
        return False

    # Test TCP Port 443
    parsed = urlparse(url)
    host = parsed.hostname or url.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
    port = parsed.port or (443 if parsed.scheme == "https" else 6333)

    print(f"[*] Step 1: Testing TCP socket reachability to '{host}:{port}'...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect((host, port))
        s.close()
        print(f"    - TCP Connection to {host}:{port} : SUCCESSFUL (Reachable)")
    except Exception as e:
        print(f"    - TCP Connection to {host}:{port} : FAILED ({e})")
        print("    -> Check your network connection or cluster domain name.")
        return False

    # Test Qdrant Client API using port=None and prefer_grpc=False
    print(f"[*] Step 2: Testing Qdrant Cloud API authentication (port=None, prefer_grpc=False)...")
    try:
        client = QdrantClient(
            url=url,
            port=None,
            prefer_grpc=False,
            api_key=api_key,
            timeout=12.0
        )
        res = client.get_collections()
        colls = [c.name for c in res.collections]
        print(f"[+] Authentication SUCCESSFUL! Cluster is active and responsive.")
        print(f"    Existing collections ({len(colls)}): {colls if colls else 'None (empty cluster, ready for ingestion)'}")

        # Check target collection
        print(f"[*] Step 3: Checking collection '{collection_name}' status...")
        if client.collection_exists(collection_name):
            info = client.get_collection(collection_name)
            v_size = info.config.params.vectors.size
            v_dist = info.config.params.vectors.distance
            points_cnt = info.points_count
            print(f"[+] Collection '{collection_name}' exists:")
            print(f"    - Points Count    : {points_cnt:,}")
            print(f"    - Vector Dimension: {v_size} (Expected: 384)")
            print(f"    - Distance Metric : {v_dist} (Expected: Cosine)")
            print(f"    - Status          : {info.status}")
        else:
            print(f"[i] Collection '{collection_name}' does not exist yet.")
            print(f"    (It will be automatically created with dim=384 and distance=Cosine during migration)")

        print("\n" + "=" * 70)
        print("RESULT: SUCCESS - Qdrant Cloud is fully connected and ready for migration!")
        print("=" * 70 + "\n")
        return True

    except UnexpectedResponse as e:
        print("\n" + "!" * 70)
        if e.status_code == 403:
            print(f"DIAGNOSIS: Authentication Failed - HTTP 403 Forbidden")
            print("The Qdrant cluster rejected your API key.")
            print("\nHOW TO FIX:")
            print("  1. Verify QDRANT_API_KEY in backend/.env.")
            print("  2. Check Qdrant Cloud Console -> Cluster -> API Keys.")
            print("  3. Make sure the API key is active and has read/write privileges.")
        else:
            print(f"Qdrant Cloud HTTP Error ({e.status_code}): {e}")
        print("!" * 70 + "\n")
        return False
    except Exception as e:
        print(f"[-] Qdrant Client Connection Error ({type(e).__name__}): {e}")
        return False


if __name__ == "__main__":
    success = test_qdrant()
    sys.exit(0 if success else 1)
