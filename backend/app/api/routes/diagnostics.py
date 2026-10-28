"""
Safe diagnostics endpoint for MongoDB Atlas TLS debugging on Render.

Activation: set ENABLE_DIAGNOSTICS=true in Render environment variables.
Deactivation: remove or set ENABLE_DIAGNOSTICS to anything other than "true".

SECURITY RULES ENFORCED IN THIS FILE:
  - Never log or return MONGODB_URI, passwords, API keys, or any secret.
  - Never disable TLS certificate verification.
  - Never expose network topology details beyond what is necessary for debugging.
  - The endpoint returns HTTP 403 unless ENABLE_DIAGNOSTICS=true is explicitly set.
"""

import os
import sys
import ssl
import socket
import logging
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Diagnostics"])


def _is_diagnostics_enabled() -> bool:
    return os.environ.get("ENABLE_DIAGNOSTICS", "").strip().lower() == "true"


def _extract_atlas_hostname(uri: str) -> str:
    """
    Extract just the SRV hostname from a mongodb+srv:// URI without
    logging or returning the username, password, or full URI.
    Returns only the cluster hostname (e.g. cluster0.s8wie4s.mongodb.net).
    """
    try:
        # Strip scheme, credentials, and path
        # mongodb+srv://user:pass@host/db?opts → host
        after_scheme = uri.split("//", 1)[-1]
        # Remove user:pass@ prefix if present
        if "@" in after_scheme:
            after_scheme = after_scheme.split("@", 1)[1]
        # Remove /database and ?options
        hostname = after_scheme.split("/")[0].split("?")[0].strip()
        return hostname or "[unparseable]"
    except Exception:
        return "[unparseable]"


def _check_dns(hostname: str) -> dict:
    try:
        addrs = socket.getaddrinfo(hostname, 27017, socket.AF_UNSPEC, socket.SOCK_STREAM)
        ips = list({a[4][0] for a in addrs})
        return {"resolved": True, "ip_count": len(ips)}
    except Exception as e:
        return {"resolved": False, "error": type(e).__name__}


def _check_tcp(hostname: str, port: int = 27017, timeout: float = 5.0) -> dict:
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
            return {"connected": True}
    except Exception as e:
        return {"connected": False, "error": f"{type(e).__name__}: {e}"}


def _check_tls(hostname: str, port: int = 27017, timeout: float = 8.0) -> dict:
    """Attempt a TLS handshake without sending MongoDB protocol bytes."""
    import certifi
    try:
        ctx = ssl.create_default_context(cafile=certifi.where())
        with socket.create_connection((hostname, port), timeout=timeout) as raw_sock:
            with ctx.wrap_socket(raw_sock, server_hostname=hostname) as tls_sock:
                peer_cert = tls_sock.getpeercert()
                subject = dict(x[0] for x in peer_cert.get("subject", []))
                issuer  = dict(x[0] for x in peer_cert.get("issuer", []))
                return {
                    "handshake": "success",
                    "protocol": tls_sock.version(),
                    "cert_subject_cn": subject.get("commonName", "unknown"),
                    "cert_issuer_o":   issuer.get("organizationName", "unknown"),
                    "cert_not_after":  peer_cert.get("notAfter", "unknown"),
                }
    except ssl.SSLCertVerificationError as e:
        return {"handshake": "cert_verification_failed", "error": str(e)}
    except ssl.SSLError as e:
        return {"handshake": "ssl_error", "error": str(e)}
    except Exception as e:
        return {"handshake": "failed", "error": f"{type(e).__name__}: {e}"}


def _check_mongodb_ping(uri: str) -> dict:
    """
    Attempt a minimal MongoDB ping. Reports success/failure and exception class.
    NEVER logs the URI or credentials.
    """
    try:
        import certifi
        from pymongo import MongoClient
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=10000,
            tlsCAFile=certifi.where(),
        )
        result = client.admin.command("ping")
        client.close()
        return {"ping": "ok", "response": result}
    except Exception as e:
        return {"ping": "failed", "error_type": type(e).__name__, "error": str(e)}


@router.get("/diagnostics")
def get_diagnostics():
    """
    Safe TLS/connectivity diagnostics for MongoDB Atlas on Render.
    Only active when ENABLE_DIAGNOSTICS=true env var is set.
    Remove this env var once the connection is confirmed working.
    """
    if not _is_diagnostics_enabled():
        raise HTTPException(
            status_code=403,
            detail="Diagnostics endpoint is disabled. Set ENABLE_DIAGNOSTICS=true to enable."
        )

    import certifi
    import pymongo

    uri = os.environ.get("MONGODB_URI", "")
    uri_present = bool(uri and uri.strip())
    uri_scheme   = uri.split("://")[0] if "://" in uri else "[no-scheme]"
    atlas_host   = _extract_atlas_hostname(uri) if uri_present else "[no-uri]"

    dns_result = _check_dns(atlas_host) if uri_present else {"skipped": "no URI"}
    tcp_result = _check_tcp(atlas_host) if uri_present else {"skipped": "no URI"}
    tls_result = _check_tls(atlas_host) if uri_present else {"skipped": "no URI"}
    ping_result = _check_mongodb_ping(uri) if uri_present else {"skipped": "no URI"}

    # Check whether SSL_CERT_FILE is set (its value may be a path — safe to show)
    ssl_cert_file = os.environ.get("SSL_CERT_FILE", "[not set]")

    return {
        "diagnostic_version": "1.0",
        "environment": {
            "python_version": sys.version,
            "openssl_version": ssl.OPENSSL_VERSION,
            "pymongo_version": pymongo.__version__,
            "certifi_version": certifi.__version__,
            "certifi_ca_bundle_path": certifi.where(),
            "SSL_CERT_FILE_env": ssl_cert_file,
        },
        "mongodb_uri": {
            "present": uri_present,
            "scheme": uri_scheme,
            "atlas_hostname": atlas_host,
            # Never include user, password, or full URI
        },
        "connectivity": {
            "dns_resolution": dns_result,
            "tcp_27017": tcp_result,
            "tls_handshake_27017": tls_result,
        },
        "mongodb_ping": ping_result,
        "note": (
            "Remove ENABLE_DIAGNOSTICS env var from Render after confirming the connection works. "
            "This endpoint never exposes secrets."
        )
    }
