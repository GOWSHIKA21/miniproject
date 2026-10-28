#!/usr/bin/env python3
"""
PatentGraph AI - Neo4j Aura Connectivity Diagnostic Tool
========================================================
Diagnoses Neo4j Aura connectivity, TLS verification, authentication,
and cluster status across both Bolt (port 7687) and HTTPS Query API (port 443).
"""

import os
import sys
import json
import base64
import socket
import ssl
import urllib.request
import logging
from pathlib import Path
from urllib.parse import urlparse

import certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

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

from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TestNeo4jConn")


def check_tcp_port(host: str, port: int, timeout: float = 4.0) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False


def test_neo4j_http_api(host: str, user: str, password: str, database: str) -> bool:
    """Test query execution using official Aura Query API over HTTPS port 443."""
    ctx = ssl.create_default_context(cafile=certifi.where())
    auth = base64.b64encode(f"{user}:{password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    url = f"https://{host}/db/{database}/query/v2"
    body = json.dumps({"statement": "RETURN 1 AS status, datetime() AS ts"}).encode()

    try:
        req = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            status_val = data.get("data", {}).get("values", [[None]])[0][0]
            print(f"[+] HTTPS Query API (Port 443): Authentication & Execution SUCCESSFUL! (status={status_val})")

        # Query node count
        body_count = json.dumps({"statement": "MATCH (n) RETURN count(n) AS total_nodes"}).encode()
        req_count = urllib.request.Request(url, data=body_count, headers=headers)
        with urllib.request.urlopen(req_count, context=ctx, timeout=8) as resp2:
            data2 = json.loads(resp2.read().decode())
            count_val = data2.get("data", {}).get("values", [[0]])[0][0]
            print(f"    Current graph size: {count_val:,} nodes in database '{database}'")

        return True
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode()
        print(f"[-] HTTPS Query API HTTP {e.code}: {err_msg}")
        return False
    except Exception as e:
        print(f"[-] HTTPS Query API error: {e}")
        return False


def test_neo4j():
    uri = os.getenv("NEO4J_URI", "neo4j+s://f53f0d18.databases.neo4j.io")
    user = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER") or "f53f0d18"
    password = os.getenv("NEO4J_PASSWORD", "")
    database = os.getenv("NEO4J_DATABASE") or user or "f53f0d18"

    print("\n" + "=" * 70)
    print("NEO4J AURA CONNECTIVITY & AUTHENTICATION DIAGNOSTIC")
    print("=" * 70)
    print(f"Target URI : {uri}")
    print(f"Username   : {user}")
    print(f"Database   : {database}")
    print(f"Password   : {'[SET - ' + str(len(password)) + ' chars]' if password else '[NOT SET]'}")
    print(f"CA Bundle  : {certifi.where()}")
    print("-" * 70)

    parsed = urlparse(uri)
    host = parsed.hostname or uri.replace("neo4j+s://", "").replace("bolt+s://", "").split(":")[0]

    # 1. Test TCP reachability
    print(f"[*] Step 1: Testing TCP socket reachability to '{host}'...")
    port_443_ok = check_tcp_port(host, 443)
    port_7687_ok = check_tcp_port(host, 7687)

    print(f"    - Port 443 (HTTPS / Query API) : {'OPEN (Reachable)' if port_443_ok else 'FAILED'}")
    print(f"    - Port 7687 (Bolt Driver)      : {'OPEN (Reachable)' if port_7687_ok else 'FIREWALL BLOCKED / REFUSED'}")

    if not password:
        print("[-] FAILED: NEO4J_PASSWORD is not set in backend/.env.")
        return False

    driver_ok = False
    # 2. Try Bolt Driver
    if port_7687_ok:
        print(f"[*] Step 2: Testing Neo4j Bolt driver connection on port 7687...")
        try:
            with GraphDatabase.driver(
                uri,
                auth=(user, password),
                connection_timeout=8.0,
                max_connection_lifetime=300,
                keep_alive=True
            ) as driver:
                driver.verify_connectivity()
                with driver.session(database=database) as session:
                    res = session.run("RETURN 1 AS status, datetime() AS ts")
                    record = res.single()
                    print(f"[+] Bolt Driver SUCCESS! (status={record['status']})")
                driver_ok = True
        except Exception as e:
            print(f"[-] Bolt driver test failed: {e}")

    # 3. Test HTTPS Query API on Port 443
    print(f"[*] Step 2: Testing Neo4j Aura official Query API over HTTPS port 443...")
    http_ok = test_neo4j_http_api(host, user, password, database)

    if driver_ok or http_ok:
        print("\n" + "=" * 70)
        mode_str = "Bolt Protocol (Port 7687)" if driver_ok else "HTTPS Query API (Port 443 - Firewall Resilient)"
        print(f"RESULT: SUCCESS - Neo4j Aura is fully connected, authorized, and operational via {mode_str}!")
        print("=" * 70 + "\n")
        return True
    else:
        print("\n" + "=" * 70)
        print("RESULT: FAILED - Could not authenticate with Neo4j Aura.")
        print("=" * 70 + "\n")
        return False


if __name__ == "__main__":
    success = test_neo4j()
    sys.exit(0 if success else 1)
