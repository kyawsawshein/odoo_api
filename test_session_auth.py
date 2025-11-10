"""Test script for session-based Odoo authentication"""

import asyncio

from app.config import settings
from app.odoo.client import OdooClient, SessionOdooClient


async def test_session_auth():
    """Test the session-based authentication system"""
    print("Testing Session-based Odoo Authentication...")

    # Create session client
    session_client = SessionOdooClient()

    # Test authentication
    try:
        print("1. Testing authentication...")
        uid = await session_client.authenticate_and_get_uid(
            url=settings.ODOO_URL,
            db=settings.ODOO_DATABASE,
            username=settings.ODOO_USERNAME,
            password=settings.ODOO_PASSWORD,
        )
        print(f"✓ Authentication successful! User ID: {uid}")

        # Test execution with session
        print("2. Testing execution with session...")
        result = await session_client.execute_with_session(
            url=settings.ODOO_URL,
            db=settings.ODOO_DATABASE,
            username=settings.ODOO_USERNAME,
            password=settings.ODOO_PASSWORD,
            uid=uid,
            model="res.partner",
            method="search",
            args=[[]],
            kwargs={"limit": 5},
        )
        print(f"✓ Session execution successful! Found {len(result)} partners")

        # Test execution without session (should re-authenticate)
        print("3. Testing execution without session...")
        result = await session_client.execute_with_session(
            url=settings.ODOO_URL,
            db=settings.ODOO_DATABASE,
            username=settings.ODOO_USERNAME,
            password=settings.ODOO_PASSWORD,
            uid=None,
            model="res.partner",
            method="search",
            args=[[]],
            kwargs={"limit": 3},
        )
        print(f"✓ Re-authentication successful! Found {len(result)} partners")

        print(
            "\n🎉 All tests passed! Session-based authentication is working correctly."
        )

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

    return True


if __name__ == "__main__":
    asyncio.run(test_session_auth())
