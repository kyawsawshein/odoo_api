# Session-Based Odoo Authentication Guide

## Overview

This implementation provides cookie-based session authentication for Odoo operations in your FastAPI application. Instead of authenticating with Odoo on every API call, the system now stores the user ID in cookies and uses it for subsequent operations.

## How It Works

### 1. Authentication Flow

1. **Login**: User authenticates with Odoo credentials via `/api/v1/auth/odoo-login`
2. **Session Storage**: The Odoo user ID (`uid`) is stored in a cookie named `odoo_user_id`
3. **Subsequent Calls**: API routes check for the `odoo_user_id` cookie and use it for Odoo operations
4. **Fallback**: If session is invalid, the system automatically re-authenticates

### 2. Key Components

#### SessionOdooClient
- Located in [`app/odoo/client.py`](app/odoo/client.py)
- Provides session-based Odoo operations
- Methods:
  - [`authenticate_and_get_uid()`](app/odoo/client.py:265) - Authenticate and return user ID for session storage
  - [`execute_with_session()`](app/odoo/client.py:272) - Execute Odoo methods using session

#### Session Authentication Middleware
- Located in [`app/auth/session_auth.py`](app/auth/session_auth.py)
- Dependencies:
  - [`get_odoo_session_user()`](app/auth/session_auth.py:12) - Get user from session cookie
  - [`get_session_odoo_connection()`](app/auth/session_auth.py:60) - Get session-based Odoo connection
  - [`require_odoo_session()`](app/auth/session_auth.py:42) - Require valid session

### 3. Updated Routes

The project API routes in [`app/project/api/v1.py`](app/project/api/v1.py) have been updated to use session-based authentication:

```python
# Before (authenticates every call)
current_user: User = Depends(get_current_user)
odoo_connection=Depends(odoo.connection)

# After (uses session)
current_user: User = Depends(get_odoo_session_user)
odoo_connection=Depends(get_session_odoo_connection)
```

### 4. Cookie Management

The login endpoint in [`app/auth/api/v1.py`](app/auth/api/v1.py:133) now sets two cookies:

- `odoo_token`: JWT token for API authentication
- `odoo_user_id`: Odoo user ID for session-based operations

### 5. Benefits

1. **Performance**: Reduces authentication overhead on subsequent calls
2. **Reliability**: Automatic re-authentication if session expires
3. **Security**: User credentials are not stored in cookies, only the user ID
4. **Compatibility**: Works with existing Odoo client infrastructure

## Usage

### For New Routes

To use session-based authentication in new routes:

```python
from app.auth.session_auth import get_odoo_session_user, get_session_odoo_connection

@router.get("/my-route")
async def my_route(
    current_user: User = Depends(get_odoo_session_user),
    odoo_connection=Depends(get_session_odoo_connection)
):
    # Use odoo_connection.execute_kw() for Odoo operations
    result = await odoo_connection.execute_kw(
        "res.partner", "search", [[]], {"limit": 10}
    )
    return result
```

### Testing

Run the test script to verify the implementation:

```bash
python test_session_auth.py
```

## Configuration

The system uses the following environment variables from your `.env` file:

- `ODOO_URL`: Odoo server URL
- `ODOO_DATABASE`: Odoo database name
- `ODOO_USERNAME`: Odoo username
- `ODOO_PASSWORD`: Odoo password

## Troubleshooting

1. **Network Errors**: Ensure Odoo server is accessible
2. **Session Expiry**: System automatically re-authenticates
3. **Cookie Issues**: Check browser cookie settings and CORS configuration
4. **Authentication Failures**: Verify Odoo credentials in environment variables