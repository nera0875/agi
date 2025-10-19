#!/usr/bin/env python3
"""
MCP Authentication Helper
Handles OAuth flows, API key validation, JWT generation, etc.
"""

import sys
import json
import time
import uuid
import hashlib
import base64
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode, quote

try:
    import requests
    import jwt
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "PyJWT", "-q"])
    import requests
    import jwt


def oauth_device_flow(
    device_code_url: str,
    token_url: str,
    client_id: str,
    scopes: list = None,
    timeout: int = 600
) -> Dict[str, str]:
    """
    OAuth 2.0 Device Flow
    Perfect for VPS (no callback needed)

    Args:
        device_code_url: URL to request device code
        token_url: URL to poll for token
        client_id: OAuth client ID
        scopes: List of scopes to request
        timeout: Max wait time in seconds

    Returns:
        {"access_token": "xxx", "refresh_token": "yyy", "expires_in": 3600}
    """
    if scopes is None:
        scopes = []

    try:
        # Step 1: Get device code
        device_request = {
            "client_id": client_id,
            "scope": " ".join(scopes)
        }

        response = requests.post(device_code_url, data=device_request, timeout=10)
        response.raise_for_status()
        device_data = response.json()

        device_code = device_data.get("device_code")
        user_code = device_data.get("user_code")
        verification_uri = device_data.get("verification_uri")
        interval = device_data.get("interval", 5)

        print("\n" + "="*60)
        print("Device Authorization Flow")
        print("="*60)
        print(f"\nPlease visit: {verification_uri}")
        print(f"And enter code: {user_code}")
        print(f"\nWaiting for authorization (up to {timeout}s)...\n")

        # Step 2: Poll for token
        start_time = time.time()
        poll_count = 0

        while time.time() - start_time < timeout:
            poll_count += 1
            time.sleep(interval)

            token_request = {
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device_code,
                "client_id": client_id
            }

            try:
                response = requests.post(token_url, data=token_request, timeout=10)

                if response.status_code == 200:
                    token_data = response.json()
                    print(f"Authorization successful! (after {poll_count} polls)")
                    return {
                        "access_token": token_data.get("access_token"),
                        "refresh_token": token_data.get("refresh_token", ""),
                        "expires_in": token_data.get("expires_in", 3600),
                        "token_type": token_data.get("token_type", "Bearer")
                    }
                elif response.status_code == 400:
                    error = response.json().get("error", "")
                    if error == "authorization_pending":
                        print(f"Poll {poll_count}: Waiting for user authorization...")
                        continue
                    elif error == "slow_down":
                        interval += 5
                        continue
                    elif error == "expired_token":
                        return {"error": "Device code expired"}

            except Exception as e:
                print(f"Poll error: {e}")
                continue

        return {"error": "Authorization timeout"}

    except Exception as e:
        return {"error": f"Device flow failed: {str(e)}"}


def oauth_client_credentials(
    token_url: str,
    client_id: str,
    client_secret: str,
    scopes: list = None
) -> Dict[str, str]:
    """
    OAuth 2.0 Client Credentials Flow
    For service-to-service authentication

    Args:
        token_url: Token endpoint URL
        client_id: OAuth client ID
        client_secret: OAuth client secret
        scopes: List of scopes to request

    Returns:
        {"access_token": "xxx", "expires_in": 3600, "token_type": "Bearer"}
    """
    if scopes is None:
        scopes = []

    try:
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }

        if scopes:
            data["scope"] = " ".join(scopes)

        response = requests.post(token_url, data=data, timeout=10)
        response.raise_for_status()

        token_data = response.json()
        return {
            "access_token": token_data.get("access_token"),
            "expires_in": token_data.get("expires_in", 3600),
            "token_type": token_data.get("token_type", "Bearer")
        }

    except Exception as e:
        return {"error": f"Client credentials flow failed: {str(e)}"}


def oauth_authorization_code(
    auth_url: str,
    token_url: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    scopes: list = None,
    state: str = None
) -> Tuple[str, str]:
    """
    OAuth 2.0 Authorization Code Flow
    Returns auth URL for user to visit and code to exchange

    Args:
        auth_url: Authorization endpoint
        token_url: Token endpoint
        client_id: OAuth client ID
        client_secret: OAuth client secret
        redirect_uri: Redirect URI
        scopes: List of scopes
        state: State parameter for CSRF protection

    Returns:
        (auth_url_to_visit, state)
    """
    if scopes is None:
        scopes = []
    if state is None:
        state = uuid.uuid4().hex

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes),
        "state": state
    }

    url = f"{auth_url}?{urlencode(params)}"
    return url, state


def exchange_authorization_code(
    token_url: str,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str
) -> Dict[str, str]:
    """
    Exchange authorization code for access token
    """
    try:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri
        }

        response = requests.post(token_url, data=data, timeout=10)
        response.raise_for_status()

        token_data = response.json()
        return {
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token", ""),
            "expires_in": token_data.get("expires_in", 3600),
            "token_type": token_data.get("token_type", "Bearer")
        }

    except Exception as e:
        return {"error": f"Code exchange failed: {str(e)}"}


def validate_api_key(
    test_url: str,
    api_key: str,
    header_name: str = "Authorization",
    timeout: int = 10
) -> Tuple[bool, str]:
    """
    Test if API key is valid by making a test request

    Args:
        test_url: URL to test against
        api_key: API key to validate
        header_name: Header name for the key (default: Authorization)
        timeout: Request timeout in seconds

    Returns:
        (is_valid, message)
    """
    try:
        headers = {header_name: api_key}
        response = requests.get(test_url, headers=headers, timeout=timeout)

        if response.status_code == 200:
            return True, f"API key valid (status {response.status_code})"
        elif response.status_code == 401 or response.status_code == 403:
            return False, f"API key rejected (status {response.status_code})"
        else:
            return None, f"Unexpected status: {response.status_code}"

    except requests.exceptions.Timeout:
        return False, "Request timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection error"
    except Exception as e:
        return False, f"Validation failed: {str(e)}"


def validate_bearer_token(
    test_url: str,
    token: str,
    timeout: int = 10
) -> Tuple[bool, str]:
    """
    Test if Bearer token is valid
    """
    return validate_api_key(test_url, f"Bearer {token}", "Authorization", timeout)


def generate_jwt(
    secret: str,
    payload: dict,
    algorithm: str = "HS256",
    expires_in: int = 3600
) -> str:
    """
    Generate JWT token

    Args:
        secret: Secret key for signing
        payload: Token payload/claims
        algorithm: Signing algorithm (HS256, RS256, etc.)
        expires_in: Token expiration in seconds

    Returns:
        JWT token string
    """
    try:
        # Add standard claims
        import time
        now = int(time.time())

        claims = {
            "iat": now,
            "exp": now + expires_in,
            **payload
        }

        token = jwt.encode(claims, secret, algorithm=algorithm)
        return token if isinstance(token, str) else token.decode()

    except Exception as e:
        raise ValueError(f"JWT generation failed: {str(e)}")


def verify_jwt(
    token: str,
    secret: str,
    algorithm: str = "HS256"
) -> Tuple[bool, dict]:
    """
    Verify and decode JWT token

    Args:
        token: JWT token string
        secret: Secret key for verification
        algorithm: Expected signing algorithm

    Returns:
        (is_valid, payload_or_error)
    """
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        return True, payload

    except jwt.ExpiredSignatureError:
        return False, {"error": "Token expired"}
    except jwt.InvalidTokenError as e:
        return False, {"error": f"Invalid token: {str(e)}"}
    except Exception as e:
        return False, {"error": f"Verification failed: {str(e)}"}


def generate_basic_auth(username: str, password: str) -> str:
    """
    Generate Basic Auth header value

    Args:
        username: Username
        password: Password

    Returns:
        Base64 encoded "username:password"
    """
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def generate_api_key(length: int = 32) -> str:
    """
    Generate a random API key

    Args:
        length: Length of the key

    Returns:
        Random hex string
    """
    import secrets
    return secrets.token_hex(length // 2)


def main():
    """CLI interface for auth helpers"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  auth_helper.py device-flow <device_code_url> <token_url> <client_id>")
        print("  auth_helper.py client-credentials <token_url> <client_id> <client_secret>")
        print("  auth_helper.py validate-key <test_url> <api_key>")
        print("  auth_helper.py generate-jwt <secret> <payload_json>")
        print("  auth_helper.py verify-jwt <token> <secret>")
        print("  auth_helper.py generate-key [length]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "device-flow" and len(sys.argv) >= 5:
        result = oauth_device_flow(sys.argv[2], sys.argv[3], sys.argv[4])
        print(json.dumps(result, indent=2))

    elif command == "client-credentials" and len(sys.argv) >= 5:
        result = oauth_client_credentials(sys.argv[2], sys.argv[3], sys.argv[4])
        print(json.dumps(result, indent=2))

    elif command == "validate-key" and len(sys.argv) >= 4:
        is_valid, msg = validate_api_key(sys.argv[2], sys.argv[3])
        print(f"Valid: {is_valid}")
        print(f"Message: {msg}")

    elif command == "generate-jwt" and len(sys.argv) >= 4:
        payload = json.loads(sys.argv[3])
        token = generate_jwt(sys.argv[2], payload)
        print(f"Token: {token}")

    elif command == "verify-jwt" and len(sys.argv) >= 4:
        is_valid, result = verify_jwt(sys.argv[2], sys.argv[3])
        print(f"Valid: {is_valid}")
        print(json.dumps(result, indent=2))

    elif command == "generate-key":
        length = int(sys.argv[2]) if len(sys.argv) > 2 else 32
        key = generate_api_key(length)
        print(f"API Key: {key}")

    else:
        print("Unknown command or missing arguments")
        sys.exit(1)


if __name__ == "__main__":
    main()
