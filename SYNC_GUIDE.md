# Sync Contacts from Odoo - Complete Guide

This guide explains how to run the `sync_contacts_from_odoo` operation to sync contacts from your external Odoo instance into the API database.

## How the Sync Works

The `sync_contacts_from_odoo` method:
1. Connects to your Odoo instance using the configured Odoo client
2. Fetches all contacts from Odoo
3. Creates or updates contacts in the local API database
4. Returns a sync response with the count of synced contacts

## Methods to Run Sync

### Method 1: Using GraphQL (Recommended)

#### Step 1: Get Authentication Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -d "username=admin&password=admin" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

Response:
```json
{
  "access_token": "your_jwt_token_here",
  "token_type": "bearer"
}
```

#### Step 2: Execute GraphQL Mutation
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token_here" \
  -d '{
    "query": "mutation { sync_contacts_from_odoo { success message odoo_id local_id errors } }"
  }'
```

### Method 2: Using REST API

```bash
curl -X POST http://localhost:8000/api/v1/contacts/sync \
  -H "Authorization: Bearer your_jwt_token_here" \
  -H "Content-Type: application/json"
```

### Method 3: Using Odoo Module (From Odoo Interface)

1. Go to **Configuration > API Integration > API Configurations**
2. Create or select an API configuration
3. Click **Test Connection** to authenticate
4. Click **Sync Contacts** to run the sync

### Method 4: Using Python Script

```python
import requests
import json

# 1. Get authentication token
auth_response = requests.post(
    "http://localhost:8000/api/v1/auth/token",
    data={"username": "admin", "password": "admin"}
)
token = auth_response.json()["access_token"]

# 2. Execute GraphQL mutation
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

graphql_query = {
    "query": """
    mutation {
        sync_contacts_from_odoo {
            success
            message
            odoo_id
            local_id
            errors
        }
    }
    """
}

response = requests.post(
    "http://localhost:8000/graphql",
    json=graphql_query,
    headers=headers
)

print(response.json())
```

## Expected Response

Successful sync response:
```json
{
  "data": {
    "sync_contacts_from_odoo": {
      "success": true,
      "message": "Successfully synced 15 contacts from Odoo",
      "odoo_id": null,
      "local_id": null,
      "errors": []
    }
  }
}
```

## What Happens During Sync

1. **Odoo Connection**: The API connects to your Odoo instance using the configured Odoo client
2. **Contact Search**: Fetches all contacts from Odoo using `search_contacts()`
3. **Data Processing**:
   - For each Odoo contact, checks if it exists in the local database by `odoo_id`
   - If exists: Updates the local record with Odoo data
   - If new: Creates a new contact in the local database
4. **Cache Clear**: Clears contact cache to ensure fresh data
5. **Response**: Returns sync statistics

## Odoo Client Configuration

Make sure your Odoo client is properly configured in the API:

### Environment Variables (.env)
```env
ODOO_URL=http://your-odoo-instance.com
ODOO_DB=your_odoo_database
ODOO_USERNAME=your_odoo_username
ODOO_PASSWORD=your_odoo_password
```

### Odoo Client Methods Used
- `search_contacts()`: Fetches contacts from Odoo
- The sync expects contacts with fields: `id`, `name`, `email`, `phone`

## Monitoring Sync Operations

### Check Sync Jobs in Odoo Module
1. Go to **API Integration > Monitoring > Sync Jobs**
2. View all sync operations with status, timestamps, and error messages

### API Logs
Check the API server logs for detailed sync information:
```bash
cd odoo_api
docker-compose logs -f
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check Odoo credentials in environment variables
   - Verify Odoo instance is accessible

2. **No Contacts Synced**
   - Check if Odoo has contacts
   - Verify Odoo client connection
   - Check API logs for errors

3. **Connection Timeout**
   - Verify Odoo URL is correct
   - Check network connectivity
   - Ensure Odoo instance is running

4. **Permission Errors**
   - Verify Odoo user has read permissions for contacts
   - Check API user permissions

### Debug Steps

1. **Test Odoo Connection**:
```python
from app.odoo.client import OdooClient

client = OdooClient()
contacts = await client.search_contacts()
print(f"Found {len(contacts)} contacts in Odoo")
```

2. **Check API Database**:
```sql
SELECT COUNT(*) FROM contacts;
SELECT * FROM contacts LIMIT 5;
```

3. **Verify Environment**:
```bash
echo $ODOO_URL
echo $ODOO_DB
```

## Automation

### Cron Job Setup
The Odoo module includes automatic cron jobs that run hourly:
- Sync Contacts: Runs `sync_contacts_from_odoo` for all active configurations
- You can modify intervals in Odoo **Settings > Technical > Scheduled Actions**

### Manual Trigger via API
You can also trigger sync via the Odoo module's REST API:
```bash
curl -X POST http://your-odoo-instance.com/api_module/sync_contacts \
  -H "Content-Type: application/json" \
  -d '{"config_id": 1}'
```

## Best Practices

1. **Regular Sync**: Set up hourly cron jobs for regular synchronization
2. **Error Handling**: Monitor sync jobs and set up alerts for failures
3. **Data Validation**: Verify synced data matches between systems
4. **Backup**: Regular database backups before major sync operations
5. **Monitoring**: Use the sync job history for performance tracking

This sync operation ensures your API database stays updated with the latest contact information from your Odoo instance.