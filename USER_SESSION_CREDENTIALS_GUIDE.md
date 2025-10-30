# User Session Odoo Credentials Implementation

This guide explains the new implementation where Odoo credentials are stored per user session instead of using environment variables.

## Overview

The system now allows each user to:
- Store their own Odoo credentials in their user profile
- Test Odoo connections before saving credentials
- Use their personal Odoo instance for sync operations
- Have isolated Odoo sessions per user

## API Endpoints

### 1. Get Odoo Credentials
```bash
GET /api/v1/profile/odoo-credentials
Authorization: Bearer <jwt_token>
```

Response:
```json
{
  "odoo_username": "admin",
  "odoo_password": "admin",
  "odoo_database": "odoo_db"
}
```

### 2. Set Odoo Credentials
```bash
POST /api/v1/profile/odoo-credentials
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "odoo_username": "admin",
  "odoo_password": "admin", 
  "odoo_database": "odoo_db"
}
```

Response:
```json
{
  "message": "Odoo credentials updated successfully",
  "odoo_uid": 1,
  "odoo_url": "http://localhost:8069",
  "odoo_database": "odoo_db"
}
```

### 3. Test Odoo Credentials (without saving)
```bash
POST /api/v1/profile/odoo-credentials/test
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "odoo_username": "admin",
  "odoo_password": "admin",
  "odoo_database": "odoo_db"
}
```

Response:
```json
{
  "message": "Odoo credentials test successful",
  "odoo_uid": 1,
  "contact_count": 15,
  "product_count": 23,
  "odoo_url": "http://localhost:8069",
  "odoo_database": "odoo_db"
}
```

### 4. Delete Odoo Credentials
```bash
DELETE /api/v1/profile/odoo-credentials
Authorization: Bearer <jwt_token>
```

Response:
```json
{
  "message": "Odoo credentials deleted successfully"
}
```

## How It Works

### Database Changes
- Added Odoo credential fields to User model:
  - `odoo_url` - Odoo instance URL
  - `odoo_database` - Odoo database name
  - `odoo_username` - Odoo username
  - `odoo_password` - Odoo password

### Service Layer Changes
- `BaseService._get_odoo_client()` now retrieves credentials from user session
- Services automatically use the current user's Odoo credentials
- Error handling for missing or invalid credentials

### Authentication Flow
1. User authenticates with API (gets JWT token)
2. User sets Odoo credentials via profile endpoints
3. All sync operations use user's Odoo credentials
4. Credentials are validated before sync operations

## Usage Examples

### Python Script Example
```python
import requests
import json

# 1. Authenticate with API
auth_response = requests.post(
    "http://localhost:8000/api/v1/auth/token",
    data={"username": "api_user", "password": "api_password"}
)
token = auth_response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# 2. Set Odoo credentials
credentials = {
    "odoo_username": "admin",
    "odoo_password": "admin",
    "odoo_database": "odoo_db"
}

response = requests.post(
    "http://localhost:8000/api/v1/profile/odoo-credentials",
    json=credentials,
    headers=headers
)
print("Credentials set:", response.json())

# 3. Run sync operations (will use user's Odoo credentials)
graphql_query = {
    "query": """
    mutation {
        sync_contacts_from_odoo {
            success
            message
        }
    }
    """
}

response = requests.post(
    "http://localhost:8000/graphql",
    json=graphql_query,
    headers=headers
)
print("Sync result:", response.json())
```

### cURL Examples

#### Set Credentials
```bash
curl -X POST http://localhost:8000/api/v1/profile/odoo-credentials \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "odoo_username": "admin",
    "odoo_password": "admin",
    "odoo_database": "odoo_db"
  }'
```

#### Test Credentials
```bash
curl -X POST http://localhost:8000/api/v1/profile/odoo-credentials/test \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "odoo_username": "admin",
    "odoo_password": "admin", 
    "odoo_database": "odoo_db"
  }'
```

#### Run Sync with User Credentials
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { sync_contacts_from_odoo { success message } }"
  }'
```

## Benefits

1. **Multi-tenant Support**: Multiple users can connect to different Odoo instances
2. **Security**: Credentials are isolated per user
3. **Flexibility**: Users can change Odoo instances without affecting others
4. **Testing**: Users can test credentials before committing
5. **Audit Trail**: Each sync operation uses specific user credentials

## Migration from Environment Variables

### Old System (Environment Variables)
```python
# Used global environment variables
ODOO_URL=http://localhost:8069
ODOO_DB=odoo_db
ODOO_USERNAME=admin
ODOO_PASSWORD=admin
```

### New System (User Session)
```python
# Uses per-user credentials stored in database
user.odoo_url = "http://localhost:8069"
user.odoo_database = "odoo_db" 
user.odoo_username = "admin"
user.odoo_password = "admin"
```

## Error Handling

### Missing Credentials
If a user tries to sync without setting Odoo credentials:
```json
{
  "success": false,
  "message": "User has no Odoo credentials configured",
  "errors": ["User has no Odoo credentials configured"]
}
```

### Invalid Credentials
If Odoo authentication fails:
```json
{
  "success": false, 
  "message": "Odoo contact sync failed: Invalid Odoo credentials",
  "errors": ["Invalid Odoo credentials"]
}
```

## Security Considerations

1. **Password Storage**: In production, Odoo passwords should be encrypted
2. **Session Management**: JWT tokens have expiration
3. **Access Control**: Users can only access their own credentials
4. **Validation**: Credentials are tested before being saved

## Integration with Odoo Module

The Odoo API module can now:
- Use different Odoo instances per configuration
- Store multiple Odoo connections
- Switch between Odoo instances dynamically
- Maintain separate sync histories per Odoo instance

This implementation provides a robust, multi-tenant solution for Odoo integration where each user can manage their own Odoo connections independently.