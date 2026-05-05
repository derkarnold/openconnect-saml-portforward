#!/usr/bin/env python3
"""CLI script to obtain a SAML token by automating a web login flow via agent-browser."""

import argparse
import json
import subprocess
import sys
import time
import requests
from typing import Any

_DEBUG_MODE = False

class BrowserAutomationException(Exception):
    """Raised when a browser automation step fails."""


def send_token_to_callback(callback_url: str, token_name: str, saml_token: str) -> None:
    """POST the SAML token to the callback URL as form data."""
    try:
        # We send the data as the token name and also a generic token parameter.
        response = requests.post(callback_url, data={token_name: saml_token, "token": saml_token}, timeout=10)
        print(f"Token sent to callback URL (HTTP {response.status_code}).")
    except requests.RequestException as exc:
        print(f"Failed to send token to callback URL: {exc}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Get a SAML token from a web login flow.")
    parser.add_argument("url", help="The login URL to navigate to.")
    parser.add_argument("token_name", help="The name of the token cookie.")
    parser.add_argument("username", help="The username for login.")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable printing agent-browser outputs.",
                        default=False)
    parser.add_argument(
        "-c", "--callback-url",
        help="Optional URL to POST the SAML token to.",
    )
    args = parser.parse_args()

    if args.debug:
        global _DEBUG_MODE
        _DEBUG_MODE = True

    # Read single-line password from stdin.
    try:
        password = input()
    except EOFError:
        sys.exit("ABORTING: No password provided on stdin.")

    try:
        saml_token = get_saml_token(args.url, args.username, password, args.token_name)
    except BrowserAutomationException as exc:
        sys.exit(f"ABORTING: {str(exc)}")

    if args.callback_url:
        send_token_to_callback(args.callback_url, saml_token, args.token_name)
    else:
        print(saml_token)


def run_agent_browser(args: list[str]) -> Any:
    """Run an agent-browser command with --json and return the parsed data payload."""
    cmd = ["agent-browser"] + args + ["--json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        raise BrowserAutomationException(
            f"agent-browser command failed (exit code {exc.returncode}): {' '.join(args)} — {exc.stdout} - {exc.stderr}"
        )
    else:
        if _DEBUG_MODE:
            print(result.stdout)
    output = result.stdout.strip()
    parsed = json.loads(output)
    if not parsed.get("success"):
        raise BrowserAutomationException(f"agent-browser command failed: {' '.join(args)} — {parsed}")
    return parsed["data"]


def close_agent_browser():
    try:
        run_agent_browser(["close"])
    except BrowserAutomationException:
        pass


def find_selector(payload_refs: dict, role: str, name: str) -> str | None:
    """Return the selector whose object params match the given role and name."""
    for selector, params in payload_refs.items():
        if params.get("role") == role and params.get("name", "").strip() == name:
            return selector
    return None


def get_current_refs() -> dict:
    """Helper to capture a snapshot and return the refs dictionary."""
    data = run_agent_browser(["snapshot", "-i"])
    return data.get("refs", {})


def get_saml_token(url: str, username: str, password: str, token_name: str) -> str:
    """Automate the login flow and return the token cookie value."""

    try:
        # Step 2
        run_agent_browser(["open", url])
        time.sleep(1)

        # Step 3
        refs = get_current_refs()

        # Step 5 — look for Username textbox first
        username_selector = find_selector(refs, role="textbox", name="Username")
        if username_selector is None:
            # Step 5 (alt) — if Username not found, look for Password textbox and skip ahead
            password_selector = find_selector(refs, role="textbox", name="Password")
            if password_selector is not None:
                # Skip to step 11
                pass
            else:
                raise BrowserAutomationException(
                    "Could not find a textbox with name='Username' or name='Password' in the initial snapshot."
                )
        else:
            # Steps 6-10
            # Step 6
            run_agent_browser(["fill", username_selector, username])

            # Step 7
            next_selector = find_selector(refs, role="button", name="Next")
            if next_selector is None:
                raise BrowserAutomationException("Could not find a button with name='Next' after filling the username.")

            # Step 8
            run_agent_browser(["click", next_selector])

            # Step 9
            time.sleep(1)
            refs = get_current_refs()

            # Step 10 — find Password textbox with retries
            password_selector = None
            for _ in range(3):  # initial + 2 retries
                password_selector = find_selector(refs, role="textbox", name="Password")
                if password_selector is not None:
                    break
                time.sleep(1)
                refs = get_current_refs()

            if password_selector is None:
                raise BrowserAutomationException("Could not find a textbox with name='Password' after clicking Next (retries exhausted).")

        # Step 11
        run_agent_browser(["fill", password_selector, password])

        # Step 12
        refs = get_current_refs()

        verify_selector = find_selector(refs, role="button", name="Verify")
        if verify_selector is None:
            raise BrowserAutomationException("Could not find a button with name='Verify' after filling the password.")

        # Step 13
        run_agent_browser(["click", verify_selector])

        # Step 14
        time.sleep(3)
        refs = get_current_refs()

        # Step 15 — find "Send Me a Push" button with retries
        push_selector = None
        for _ in range(3):  # initial + 2 retries
            push_selector = find_selector(refs, role="button", name="Send Me a Push")
            if push_selector is not None:
                break
            time.sleep(1)
            refs = get_current_refs()

        if push_selector is None:
            raise BrowserAutomationException("Could not find a button with name='Send Me a Push' (retries exhausted).")

        # Step 13 (second occurrence — click the push button)
        run_agent_browser(["click", push_selector])

        # Step 14 (second occurrence)
        time.sleep(3)

        # Step 15 (second occurrence) — retrieve cookies
        cookies_data = None
        for attempt in range(11):  # initial + 10 retries
            cookies_data = run_agent_browser(["cookies"])
            cookies = cookies_data.get("cookies", [])
            for cookie in cookies:
                if cookie.get("name") == token_name:
                    return cookie["value"]
            if attempt < 10:
                time.sleep(1)

        raise BrowserAutomationException("Could not find the token cookie after 10 retries.")
    finally:
        close_agent_browser()


if __name__ == "__main__":
    main()

