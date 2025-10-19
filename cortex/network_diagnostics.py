#!/usr/bin/env python3
"""
Network Diagnostics for MCP Installation
Tests connectivity, DNS, ports, and proxies
"""

import sys
import socket
import subprocess
import time
from typing import Tuple, Dict, List
from pathlib import Path


def check_reachability(
    host: str,
    port: int = 443,
    timeout: int = 5,
    protocol: str = "tcp"
) -> Tuple[bool, str]:
    """
    Check if host:port is reachable

    Args:
        host: Hostname or IP address
        port: Port number (default 443 for HTTPS)
        timeout: Connection timeout in seconds
        protocol: "tcp" or "icmp"

    Returns:
        (success, message)
    """
    try:
        if protocol == "icmp":
            # Use ping
            cmd = ["ping", "-c", "1", "-W", str(timeout * 1000), host]
            result = subprocess.run(cmd, capture_output=True, timeout=timeout + 2)
            if result.returncode == 0:
                return True, f"Host {host} reachable (ping successful)"
            else:
                return False, f"Host {host} unreachable (ping failed)"

        # TCP connection test
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        try:
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                return True, f"Connection to {host}:{port} successful"
            else:
                return False, f"Connection to {host}:{port} refused (error {result})"

        except socket.gaierror:
            return False, f"DNS resolution failed for {host}"
        except socket.timeout:
            return False, f"Connection timeout to {host}:{port}"

    except Exception as e:
        return False, f"Reachability check failed: {str(e)}"


def check_port_available(port: int) -> Tuple[bool, str]:
    """
    Check if port is available for binding

    Args:
        port: Port number to check

    Returns:
        (is_available, message)
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            sock.bind(("0.0.0.0", port))
            sock.close()
            return True, f"Port {port} is available"
        except OSError:
            sock.close()
            return False, f"Port {port} is already in use"

    except Exception as e:
        return False, f"Port check failed: {str(e)}"


def test_dns(domain: str, record_type: str = "A") -> Tuple[bool, str]:
    """
    Test DNS resolution

    Args:
        domain: Domain name to resolve
        record_type: DNS record type (A, AAAA, MX, etc.)

    Returns:
        (success, message)
    """
    try:
        # Try socket resolution first (fastest)
        try:
            ip = socket.gethostbyname(domain)
            return True, f"DNS resolution successful: {domain} -> {ip}"
        except socket.gaierror:
            pass

        # Try nslookup if available
        cmd = ["nslookup", domain]
        result = subprocess.run(cmd, capture_output=True, timeout=5, text=True)

        if result.returncode == 0 and "Address" in result.stdout:
            return True, f"DNS resolution successful (via nslookup)"
        else:
            return False, f"DNS resolution failed for {domain}"

    except subprocess.TimeoutExpired:
        return False, "DNS query timeout"
    except Exception as e:
        return False, f"DNS test failed: {str(e)}"


def check_internet() -> Tuple[bool, str]:
    """
    Check internet connectivity by testing common DNS servers

    Returns:
        (is_connected, message)
    """
    dns_servers = [
        ("8.8.8.8", 53, "Google DNS"),
        ("1.1.1.1", 53, "Cloudflare DNS"),
        ("9.9.9.9", 53, "Quad9 DNS"),
    ]

    for ip, port, name in dns_servers:
        is_reachable, msg = check_reachability(ip, port, timeout=3)
        if is_reachable:
            return True, f"Internet connectivity OK ({name})"

    return False, "No internet connectivity detected"


def test_proxy(proxy_url: str) -> Tuple[bool, str]:
    """
    Test if proxy is working

    Args:
        proxy_url: Proxy URL (e.g., http://proxy.example.com:8080)

    Returns:
        (is_working, message)
    """
    try:
        # Parse proxy URL
        from urllib.parse import urlparse
        parsed = urlparse(proxy_url)

        if not parsed.hostname:
            return False, "Invalid proxy URL"

        host = parsed.hostname
        port = parsed.port or 8080

        # Test connectivity to proxy
        is_reachable, msg = check_reachability(host, port, timeout=5)

        if not is_reachable:
            return False, f"Cannot reach proxy: {msg}"

        # Try to use proxy for a test request
        try:
            import requests
            proxies = {"http": proxy_url, "https": proxy_url}
            response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=5)
            if response.status_code == 200:
                return True, f"Proxy {proxy_url} is working"
        except Exception as e:
            return False, f"Proxy test request failed: {str(e)}"

        return True, f"Proxy {proxy_url} is reachable"

    except Exception as e:
        return False, f"Proxy test failed: {str(e)}"


def test_tls_certificate(
    host: str,
    port: int = 443,
    timeout: int = 5
) -> Dict[str, any]:
    """
    Check TLS certificate validity

    Args:
        host: Hostname
        port: Port (default 443)
        timeout: Connection timeout

    Returns:
        Certificate info or error
    """
    try:
        import ssl
        context = ssl.create_default_context()

        with socket.create_connection((host, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()

                # Extract relevant info
                subject = dict(x[0] for x in cert['subject'])
                issued_to = subject.get('commonName', 'Unknown')

                return {
                    "valid": True,
                    "issued_to": issued_to,
                    "issuer": dict(x[0] for x in cert['issuer']).get('commonName', 'Unknown'),
                    "version": cert.get('version'),
                    "serial": cert.get('serialNumber')
                }

    except ssl.SSLError as e:
        return {"valid": False, "error": f"SSL error: {str(e)}"}
    except Exception as e:
        return {"valid": False, "error": f"Certificate check failed: {str(e)}"}


def get_network_info() -> Dict[str, any]:
    """
    Get system network information

    Returns:
        Dictionary with network info
    """
    try:
        # Get hostname
        hostname = socket.gethostname()

        # Get all IP addresses
        ips = []
        try:
            result = subprocess.run(
                ["hostname", "-I"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                ips = result.stdout.strip().split()
        except:
            # Fallback: get localhost
            try:
                ips = [socket.gethostbyname(hostname)]
            except:
                pass

        # Get default gateway
        gateway = None
        try:
            result = subprocess.run(
                ["ip", "route", "show"],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.split('\n'):
                if 'default via' in line:
                    gateway = line.split()[2]
                    break
        except:
            pass

        return {
            "hostname": hostname,
            "ips": ips,
            "gateway": gateway
        }

    except Exception as e:
        return {"error": str(e)}


def run_diagnostics(verbose: bool = False) -> Dict[str, any]:
    """
    Run full network diagnostics

    Args:
        verbose: Print detailed output

    Returns:
        Dictionary with all diagnostic results
    """
    results = {
        "timestamp": time.time(),
        "tests": {}
    }

    tests = [
        ("Internet Connectivity", lambda: check_internet()),
        ("Google DNS (8.8.8.8:53)", lambda: check_reachability("8.8.8.8", 53)),
        ("Cloudflare DNS (1.1.1.1:53)", lambda: check_reachability("1.1.1.1", 53)),
        ("Port 80 (HTTP)", lambda: check_port_available(80)),
        ("Port 443 (HTTPS)", lambda: check_port_available(443)),
        ("DNS Resolution (google.com)", lambda: test_dns("google.com")),
    ]

    for test_name, test_func in tests:
        try:
            success, message = test_func()
            results["tests"][test_name] = {
                "success": success,
                "message": message
            }
            if verbose:
                status = "OK" if success else "FAIL"
                print(f"[{status}] {test_name}: {message}")
        except Exception as e:
            results["tests"][test_name] = {
                "success": False,
                "message": f"Test error: {str(e)}"
            }
            if verbose:
                print(f"[ERR] {test_name}: {str(e)}")

    # Add system info
    results["network_info"] = get_network_info()

    return results


def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  network_diagnostics.py check-reachability <host> [port]")
        print("  network_diagnostics.py check-port <port>")
        print("  network_diagnostics.py test-dns <domain>")
        print("  network_diagnostics.py check-internet")
        print("  network_diagnostics.py test-proxy <proxy_url>")
        print("  network_diagnostics.py test-tls <host> [port]")
        print("  network_diagnostics.py diagnostics")
        print("  network_diagnostics.py network-info")
        sys.exit(1)

    command = sys.argv[1]

    if command == "check-reachability":
        if len(sys.argv) < 3:
            print("Error: host required")
            sys.exit(1)
        host = sys.argv[2]
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 443
        success, message = check_reachability(host, port)
        print(f"Reachability: {'OK' if success else 'FAIL'}")
        print(f"Message: {message}")
        sys.exit(0 if success else 1)

    elif command == "check-port":
        if len(sys.argv) < 3:
            print("Error: port required")
            sys.exit(1)
        port = int(sys.argv[2])
        available, message = check_port_available(port)
        print(f"Port {port}: {'Available' if available else 'In use'}")
        print(f"Message: {message}")
        sys.exit(0 if available else 1)

    elif command == "test-dns":
        if len(sys.argv) < 3:
            print("Error: domain required")
            sys.exit(1)
        domain = sys.argv[2]
        success, message = test_dns(domain)
        print(f"DNS Resolution: {'OK' if success else 'FAIL'}")
        print(f"Message: {message}")
        sys.exit(0 if success else 1)

    elif command == "check-internet":
        success, message = check_internet()
        print(f"Internet: {'Connected' if success else 'Disconnected'}")
        print(f"Message: {message}")
        sys.exit(0 if success else 1)

    elif command == "test-proxy":
        if len(sys.argv) < 3:
            print("Error: proxy URL required")
            sys.exit(1)
        proxy_url = sys.argv[2]
        success, message = test_proxy(proxy_url)
        print(f"Proxy: {'Working' if success else 'Failed'}")
        print(f"Message: {message}")
        sys.exit(0 if success else 1)

    elif command == "test-tls":
        if len(sys.argv) < 3:
            print("Error: host required")
            sys.exit(1)
        host = sys.argv[2]
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 443
        result = test_tls_certificate(host, port)
        print(f"TLS Certificate:")
        import json
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("valid") else 1)

    elif command == "diagnostics":
        verbose = "--verbose" in sys.argv or "-v" in sys.argv
        results = run_diagnostics(verbose=verbose)
        import json
        print(json.dumps(results, indent=2))

    elif command == "network-info":
        info = get_network_info()
        import json
        print(json.dumps(info, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
