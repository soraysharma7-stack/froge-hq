"""Signup / member-account tests: validation, hashing, login, durability restore.

NOTE: this module pins owner credentials, so it must run in its own pytest
process (e.g. `pytest app/tests/test_signup.py`) to avoid leaking env into
other test modules.
"""
import os

os.environ["FROGE_OWNER_EMAIL"] = "owner@froge.test"
os.environ["FROGE_OWNER_PASSWORD"] = "owner-secret-123"

from app import auth  # noqa: E402
from app.config.settings import settings  # noqa: E402

# The settings singleton may have been created by an earlier test module with
# empty owner credentials; pin the owner login for these tests.
settings.owner_email = "owner@froge.test"
settings.owner_password = "owner-secret-123"


def test_create_account_hashed_and_listed():
    auth._ACCOUNTS.clear()
    acc = auth.create_account("maya@froge.dev", "password123", "Maya")
    assert acc["email"] == "maya@froge.dev"
    stored = auth._ACCOUNTS["maya@froge.dev"]
    assert stored["password_hash"] != "password123"
    assert stored["salt"]
    listed = auth.list_accounts()
    assert listed[0]["email"] == "maya@froge.dev"
    assert "password_hash" not in listed[0]


def test_signup_validation():
    auth._ACCOUNTS.clear()
    for bad_email in ["", "nope", "a@b"]:
        try:
            auth.create_account(bad_email, "password123")
            assert False, f"expected ValueError for {bad_email!r}"
        except ValueError:
            pass
    try:
        auth.create_account("short@froge.dev", "short")
        assert False, "expected ValueError for short password"
    except ValueError:
        pass


def test_duplicate_account_rejected_and_owner_collision():
    auth._ACCOUNTS.clear()
    auth.create_account("dup@froge.dev", "password123")
    try:
        auth.create_account("dup@froge.dev", "password123")
        assert False, "expected duplicate rejection"
    except ValueError:
        pass
    try:
        auth.create_account("owner@froge.test", "password123")
        assert False, "expected owner-email collision rejection"
    except ValueError:
        pass


def test_login_owner_and_member():
    auth._ACCOUNTS.clear()
    assert auth.verify_credentials("owner@froge.test", "owner-secret-123")
    auth.create_account("member@froge.dev", "password123")
    assert auth.verify_credentials("member@froge.dev", "password123")
    assert not auth.verify_credentials("member@froge.dev", "wrong-pass")
    assert not auth.verify_credentials("ghost@froge.dev", "password123")


def test_account_restore():
    auth._ACCOUNTS.clear()
    doc = {
        "email": "restored@froge.dev",
        "name": "R",
        "password_hash": auth._hash_password("password123", "00" * 16),
        "salt": "00" * 16,
        "role": "member",
        "created_at": 1.0,
    }
    auth.restore_account(doc)
    assert auth.verify_account("restored@froge.dev", "password123")
