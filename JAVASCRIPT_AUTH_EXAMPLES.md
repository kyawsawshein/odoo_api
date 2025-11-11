# JavaScript API Authentication Examples

## Overview

This guide shows how to call your FastAPI authentication endpoints from JavaScript. You have two main authentication methods:

1. **Basic API Authentication** (`/api/v1/auth/token`) - For API users
2. **Odoo Session Authentication** (`/api/v1/auth/odoo-login`) - For Odoo users with session cookies

## 1. Basic API Authentication (`/api/v1/auth/token`)

This endpoint uses OAuth2 password flow and returns a JWT token.

### JavaScript Example

```javascript
// Function to login with API credentials
async function loginWithApiCredentials(username, password) {
    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        formData.append('client_id', 'your-client-id'); // Optional

        const response = await fetch('/api/v1/auth/token', {
            method: 'POST',
            body: formData,
            credentials: 'include' // Important for cookies
        });

        if (!response.ok) {
            throw new Error(`Login failed: ${response.statusText}`);
        }

        const data = await response.json();
        
        // Store the token for future API calls
        localStorage.setItem('api_token', data.access_token);
        
        console.log('Login successful:', data);
        return data;
        
    } catch (error) {
        console.error('Login error:', error);
        throw error;
    }
}

// Usage
loginWithApiCredentials('your-api-username', 'your-api-password')
    .then(data => {
        console.log('Token received:', data.access_token);
    })
    .catch(error => {
        console.error('Login failed:', error);
    });
```

### Using the Token for API Calls

```javascript
// Function to make authenticated API calls
async function makeAuthenticatedApiCall(url, options = {}) {
    const token = localStorage.getItem('api_token');
    
    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
    };

    const response = await fetch(url, {
        ...options,
        headers,
        credentials: 'include'
    });

    if (!response.ok) {
        throw new Error(`API call failed: ${response.statusText}`);
    }

    return await response.json();
}

// Example usage
async function getProjects() {
    try {
        const projects = await makeAuthenticatedApiCall('/api/v1/projects');
        console.log('Projects:', projects);
        return projects;
    } catch (error) {
        console.error('Failed to fetch projects:', error);
    }
}
```

## 2. Odoo Session Authentication (`/api/v1/auth/odoo-login`)

This endpoint requires API authentication first, then authenticates with Odoo and sets session cookies.

### Two-Step Authentication Flow

```javascript
// Step 1: Authenticate with API first
async function authenticateWithApi(apiUsername, apiPassword) {
    try {
        const formData = new FormData();
        formData.append('username', apiUsername);
        formData.append('password', apiPassword);

        const response = await fetch('/api/v1/auth/token', {
            method: 'POST',
            body: formData,
            credentials: 'include' // Important for cookies
        });

        if (!response.ok) {
            throw new Error(`API authentication failed: ${response.statusText}`);
        }

        const data = await response.json();
        
        // Store the API token for future calls
        localStorage.setItem('api_token', data.access_token);
        
        console.log('API authentication successful');
        return data;
        
    } catch (error) {
        console.error('API authentication error:', error);
        throw error;
    }
}

// Step 2: Then authenticate with Odoo using API token
async function loginWithOdooCredentials(odooUsername, odooPassword) {
    try {
        // Get the API token from storage
        const apiToken = localStorage.getItem('api_token');
        if (!apiToken) {
            throw new Error('API token not found. Please authenticate with API first.');
        }

        const credentials = {
            odoo_username: odooUsername,
            odoo_password: odooPassword
        };

        const response = await fetch('/api/v1/auth/odoo-login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiToken}` // Include API token
            },
            body: JSON.stringify(credentials),
            credentials: 'include' // Crucial for cookies to be stored
        });

        if (!response.ok) {
            throw new Error(`Odoo login failed: ${response.statusText}`);
        }

        const data = await response.json();
        
        console.log('Odoo login successful:', data);
        return data;
        
    } catch (error) {
        console.error('Odoo login error:', error);
        throw error;
    }
}

// Complete authentication flow
async function completeAuthenticationFlow(apiUsername, apiPassword, odooUsername, odooPassword) {
    try {
        // Step 1: API authentication
        console.log('Step 1: Authenticating with API...');
        await authenticateWithApi(apiUsername, apiPassword);
        
        // Step 2: Odoo authentication
        console.log('Step 2: Authenticating with Odoo...');
        const odooResult = await loginWithOdooCredentials(odooUsername, odooPassword);
        
        console.log('Complete authentication successful!');
        return odooResult;
        
    } catch (error) {
        console.error('Authentication flow failed:', error);
        throw error;
    }
}

// Usage
completeAuthenticationFlow(
    'your-api-username',
    'your-api-password',
    'odoo-username',
    'odoo-password'
)
.then(data => {
    console.log('Odoo User ID:', data.odoo_user_id);
    console.log('JWT Token:', data.jwt_token);
    console.log('Login Parameter:', data.login); // Store this for API calls
})
.catch(error => {
    console.error('Authentication failed:', error);
});
```

### Making Session-Based API Calls

After Odoo login, cookies are automatically sent with requests. The API now requires a `login` parameter for session-based Odoo connections:

```javascript
// Function to make session-based API calls with login parameter
async function makeSessionApiCall(url, login, options = {}) {
    // Add login parameter to URL if not already present
    const separator = url.includes('?') ? '&' : '?';
    const urlWithLogin = `${url}${separator}login=${encodeURIComponent(login)}`;
    
    const response = await fetch(urlWithLogin, {
        ...options,
        credentials: 'include' // Automatically sends cookies
    });

    if (!response.ok) {
        throw new Error(`API call failed: ${response.statusText}`);
    }

    return await response.json();
}

// Example: Get projects using session authentication
async function getProjectsWithSession(login) {
    try {
        const projects = await makeSessionApiCall('/api/v1/projects', login);
        console.log('Projects:', projects);
        return projects;
    } catch (error) {
        console.error('Failed to fetch projects:', error);
    }
}

// Example: Create project using session authentication
async function createProject(projectData, login) {
    try {
        const result = await makeSessionApiCall('/api/v1/projects', login, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(projectData)
        });
        console.log('Project created:', result);
        return result;
    } catch (error) {
        console.error('Failed to create project:', error);
    }
}

// Example: Get project by ID
async function getProjectById(projectId, login) {
    try {
        const project = await makeSessionApiCall(`/api/v1/projects/${projectId}`, login);
        console.log('Project:', project);
        return project;
    } catch (error) {
        console.error('Failed to fetch project:', error);
    }
}

// Example: Get project tasks
async function getProjectTasks(projectId, login) {
    try {
        const tasks = await makeSessionApiCall(`/api/v1/projects/${projectId}/tasks`, login);
        console.log('Tasks:', tasks);
        return tasks;
    } catch (error) {
        console.error('Failed to fetch tasks:', error);
    }
}
```

## 3. Complete Authentication Flow Example

```javascript
class OdooApiClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
        this.isAuthenticated = false;
        this.apiToken = null;
        this.login = null; // Store login parameter for API calls
    }

    // Step 1: API authentication
    async apiLogin(username, password) {
        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            const response = await fetch(`${this.baseUrl}/api/v1/auth/token`, {
                method: 'POST',
                body: formData,
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`API authentication failed: ${response.statusText}`);
            }

            const data = await response.json();
            this.apiToken = data.access_token;
            
            console.log('API authentication successful');
            return data;
            
        } catch (error) {
            console.error('API authentication error:', error);
            throw error;
        }
    }

    // Step 2: Odoo login with session cookies (requires API token)
    async odooLogin(username, password) {
        try {
            if (!this.apiToken) {
                throw new Error('API token not found. Please call apiLogin() first.');
            }

            const response = await fetch(`${this.baseUrl}/api/v1/auth/odoo-login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiToken}`
                },
                body: JSON.stringify({
                    odoo_username: username,
                    odoo_password: password
                }),
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`Odoo login failed: ${response.statusText}`);
            }

            const data = await response.json();
            this.isAuthenticated = true;
            this.login = data.login || username; // Store login parameter for API calls
            
            console.log('Odoo login successful');
            return data;
            
        } catch (error) {
            console.error('Odoo login error:', error);
            this.isAuthenticated = false;
            throw error;
        }
    }

    // Generic API call with session and login parameter
    async apiCall(endpoint, options = {}) {
        if (!this.isAuthenticated) {
            throw new Error('Not authenticated. Please login first.');
        }

        if (!this.login) {
            throw new Error('Login parameter not found. Please complete Odoo login first.');
        }

        // Add login parameter to URL
        const separator = endpoint.includes('?') ? '&' : '?';
        const urlWithLogin = `${this.baseUrl}${endpoint}${separator}login=${encodeURIComponent(this.login)}`;

        const response = await fetch(urlWithLogin, {
            ...options,
            credentials: 'include'
        });

        if (!response.ok) {
            if (response.status === 401) {
                this.isAuthenticated = false;
                throw new Error('Session expired. Please login again.');
            }
            throw new Error(`API call failed: ${response.statusText}`);
        }

        return await response.json();
    }

    // Project operations
    async getProjects() {
        return this.apiCall('/api/v1/projects');
    }

    async createProject(projectData) {
        return this.apiCall('/api/v1/projects', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(projectData)
        });
    }

    async getCurrentUser() {
        return this.apiCall('/api/v1/auth/me');
    }
}

// Usage example
const apiClient = new OdooApiClient(); // Use empty string if same domain

// Two-step authentication flow
apiClient.apiLogin('your-api-username', 'your-api-password')
    .then(() => {
        // Now authenticate with Odoo
        return apiClient.odooLogin('your-odoo-username', 'your-odoo-password');
    })
    .then(() => {
        // Now you can make authenticated calls
        return apiClient.getProjects();
    })
    .then(projects => {
        console.log('Projects:', projects);
        return apiClient.getCurrentUser();
    })
    .then(user => {
        console.log('Current user:', user);
    })
    .catch(error => {
        console.error('Error:', error);
    });
```

## 4. Important Notes

### CORS Configuration
Ensure your FastAPI CORS settings allow your frontend domain:
```python
# In your FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-frontend-domain.com"],
    allow_credentials=True,  # Important for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Cookie Security
- Cookies are set as `httponly` for security
- Set `secure=True` in production with HTTPS
- Cookies have 24-hour expiration

### Login Parameter Requirement
- All session-based API calls now require a `login` parameter
- The login parameter should be passed as a URL query parameter: `?login=username`
- This parameter is used to retrieve the correct session token from cookies
- Store the login value returned from the Odoo login response

### Error Handling
Always handle authentication errors:
```javascript
// Check if user is authenticated
function checkAuthentication(login) {
    if (!login) {
        return false;
    }
    // Make a simple API call with login parameter
    return fetch(`/api/v1/auth/me?login=${encodeURIComponent(login)}`, {
        credentials: 'include'
    })
    .then(response => response.ok)
    .catch(() => false);
}

// Handle session expiration
function handleSessionExpiration() {
    // Clear stored credentials
    localStorage.removeItem('api_token');
    // Redirect to login page or show login modal
    window.location.href = '/login';
}
```

This JavaScript implementation will work with your session-based Odoo authentication system, automatically using the cookies for subsequent API calls after login. Remember to include the `login` parameter in all session-based API calls.